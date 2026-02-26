import asyncio
import pandas as pd
import os
from dotenv import load_dotenv
from graph_client import get_graph_client
from msgraph.generated.models.user import User
from msgraph.generated.models.password_profile import PasswordProfile

# Charge les variables depuis .env
load_dotenv("../.env")

TENANT_ID     = os.environ.get("ARM_TENANT_ID")
CLIENT_ID     = os.environ.get("ARM_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET")
DOMAIN        = "brsankaraoutlook.onmicrosoft.com"

# Mapping départements → groupes Azure AD
GROUP_MAPPING = {
    "IT":  "GRP-IT",
    "DEV": "GRP-DEV",
    "RH":  "GRP-RH"
}

def build_upn(row):
    if pd.notna(row["GivenName"]) and pd.notna(row["Surname"]):
        return f"{row['GivenName'].lower()}.{row['Surname'].lower()}@{DOMAIN}"
    else:
        return f"{row['SamAccountName'].lower()}@{DOMAIN}"

async def migrate_user(client, row, group_map):
    upn = build_upn(row)
    display_name = f"{row['GivenName']} {row['Surname']}" if pd.notna(row["GivenName"]) else row["SamAccountName"]

    print(f"🔄 Vérification : {upn}")

    # Skip si désactivé
    if str(row["Enabled"]).strip() == "False":
        print(f"⏭️  Désactivé, skip : {upn}")
        return {"upn": upn, "status": "skipped", "reason": "disabled"}

    # Vérifie si existe déjà
    try:
        existing = await client.users.by_user_id(upn).get()
        if existing:
            print(f"⚠️  Déjà existant, skip : {upn}")
            return {"upn": upn, "status": "skipped", "reason": "already_exists"}
    except Exception:
        pass

    # Crée l'utilisateur
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

        # Assigne au groupe
        dept = str(row["Department"]) if pd.notna(row["Department"]) else None
        group_name = GROUP_MAPPING.get(dept)
        if group_name and group_name in group_map:
            try:
                from msgraph.generated.models.reference_create import ReferenceCreate
                azure_user = await client.users.by_user_id(upn).get()
                ref = ReferenceCreate(
                    odata_id=f"https://graph.microsoft.com/v1.0/directoryObjects/{azure_user.id}"
                )
                await client.groups.by_group_id(group_map[group_name]).members.ref.post(ref)
                print(f"   → Assigné à {group_name}")
            except Exception as e:
                print(f"   ⚠️ Erreur groupe : {e}")

        return {"upn": upn, "status": "success"}
    except Exception as e:
        print(f"❌ Erreur : {upn} → {e}")
        return {"upn": upn, "status": "failed", "error": str(e)}

async def main():
    print("🚀 Migration réelle AD on-premise → Azure AD")
    print(f"   Source  : lutin.fr")
    print(f"   Cible   : {DOMAIN}\n")

    if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Variables d'environnement manquantes !")
        return

    df = pd.read_csv("../data/on_premise_real.csv")
    print(f"📋 {len(df)} utilisateurs trouvés dans l'AD on-premise\n")

    client = get_graph_client(TENANT_ID, CLIENT_ID, CLIENT_SECRET)

    # Récupère les groupes Azure AD
    groups = await client.groups.get()
    group_map = {g.display_name: g.id for g in groups.value}

    results = {"success": [], "skipped": [], "failed": []}

    for _, row in df.iterrows():
        result = await migrate_user(client, row, group_map)
        results[result["status"]].append(result)

    print(f"\n📊 Résumé migration réelle :")
    print(f"   ✅ Migrés    : {len(results['success'])}")
    print(f"   ⏭️  Skippés  : {len(results['skipped'])}")
    print(f"   ❌ Échoués   : {len(results['failed'])}")

if __name__ == "__main__":
    asyncio.run(main())