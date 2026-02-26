import asyncio
import pandas as pd
import os
import json
import sys
from dotenv import load_dotenv
from graph_client import get_graph_client
from msgraph.generated.models.user import User
from msgraph.generated.models.password_profile import PasswordProfile
from msgraph.generated.models.reference_create import ReferenceCreate

load_dotenv("../.env")

TENANT_ID     = os.environ.get("ARM_TENANT_ID")
CLIENT_ID     = os.environ.get("ARM_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET")
DOMAIN        = "brsankaraoutlook.onmicrosoft.com"

GROUP_MAPPING = {
    "IT":  "GRP-IT",
    "DEV": "GRP-DEV",
    "RH":  "GRP-RH",
    "FINANCE": "GRP-FINANCE",
    "MANAGEMENT": "GRP-MANAGEMENT"
}

def load_config(env: str) -> dict:
    config_path = f"../environments/{env}/config.json"
    with open(config_path, "r") as f:
        return json.load(f)

def build_upn(row) -> str:
    if pd.notna(row["GivenName"]) and pd.notna(row["Surname"]):
        return f"{row['GivenName'].lower()}.{row['Surname'].lower()}@{DOMAIN}"
    return f"{row['SamAccountName'].lower()}@{DOMAIN}"

async def ensure_group_exists(client, group_name: str) -> str:
    groups = await client.groups.get()
    for g in groups.value:
        if g.display_name == group_name:
            return g.id

    # Crée le groupe s'il n'existe pas
    from msgraph.generated.models.group import Group
    new_group = Group(
        display_name=group_name,
        mail_nickname=group_name.replace(" ", "-").lower(),
        security_enabled=True,
        mail_enabled=False
    )
    created = await client.groups.post(new_group)
    print(f"   📁 Groupe créé : {group_name}")
    return created.id

async def migrate_user(client, row, config: dict, group_map: dict) -> dict:
    upn = build_upn(row)
    prefix = config["group_prefix"]
    display_name = f"{row['GivenName']} {row['Surname']}" if pd.notna(row["GivenName"]) else row["SamAccountName"]

    print(f"🔄 [{config['environment'].upper()}] Vérification : {upn}")

    if str(row["Enabled"]).strip() == "False":
        print(f"⏭️  Désactivé, skip : {upn}")
        return {"upn": upn, "status": "skipped", "reason": "disabled"}

    try:
        existing = await client.users.by_user_id(upn).get()
        if existing:
            print(f"⚠️  Déjà existant, skip : {upn}")
            return {"upn": upn, "status": "skipped", "reason": "already_exists"}
    except Exception:
        pass

    try:
        new_user = User(
            display_name=display_name,
            user_principal_name=upn,
            mail_nickname=upn.split("@")[0],
            department=str(row["Department"]) if pd.notna(row["Department"]) else None,
            job_title=str(row["Title"]) if pd.notna(row["Title"]) else None,
            account_enabled=True,
            password_profile=PasswordProfile(
                password="TempMigration123!",
                force_change_password_next_sign_in=True
            )
        )
        await client.users.post(new_user)
        print(f"✅ Migré : {upn}")
        await asyncio.sleep(8)

        # Assigne au groupe avec prefix d'environnement
        dept = str(row["Department"]) if pd.notna(row["Department"]) else None
        base_group = GROUP_MAPPING.get(dept)
        if base_group:
            group_name = f"{prefix}{base_group}" if prefix else base_group
            group_id = await ensure_group_exists(client, group_name)
            try:
                azure_user = await client.users.by_user_id(upn).get()
                ref = ReferenceCreate(
                    odata_id=f"https://graph.microsoft.com/v1.0/directoryObjects/{azure_user.id}"
                )
                await client.groups.by_group_id(group_id).members.ref.post(ref)
                print(f"   → Assigné à {group_name}")
            except Exception as e:
                print(f"   ⚠️ Erreur groupe : {e}")

        return {"upn": upn, "status": "success"}
    except Exception as e:
        print(f"❌ Erreur : {upn} → {e}")
        return {"upn": upn, "status": "failed", "error": str(e)}

async def main(env: str):
    config = load_config(env)

    print(f"🌍 Environnement  : {config['environment'].upper()}")
    print(f"📝 Description    : {config['description']}")
    print(f"👥 Max users      : {'Tous' if config['max_users'] == -1 else config['max_users']}")
    print(f"🏷️  Prefix groupes : '{config['group_prefix']}'\n")

    if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Variables d'environnement manquantes !")
        return

    df = pd.read_csv("../data/on_premise_real.csv")

    # Limite les users en DEV
    if config["max_users"] != -1:
        df = df.head(config["max_users"])
        print(f"⚠️  Mode DEV : limité à {config['max_users']} users\n")

    print(f"📋 {len(df)} utilisateurs à migrer\n")

    client = get_graph_client(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    groups = await client.groups.get()
    group_map = {g.display_name: g.id for g in groups.value}

    results = {"success": [], "skipped": [], "failed": []}

    for _, row in df.iterrows():
        result = await migrate_user(client, row, config, group_map)
        results[result["status"]].append(result)

    print(f"\n📊 Résumé [{config['environment'].upper()}] :")
    print(f"   ✅ Migrés    : {len(results['success'])}")
    print(f"   ⏭️  Skippés  : {len(results['skipped'])}")
    print(f"   ❌ Échoués   : {len(results['failed'])}")

    # Échoue si des erreurs en prod
    if config["environment"] == "prod" and len(results["failed"]) > 0:
        print("\n❌ Échecs détectés en PROD ! Pipeline arrêté.")
        sys.exit(1)

if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "dev"
    asyncio.run(main(env))