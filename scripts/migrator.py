import json
import asyncio
import os
from graph_client import get_graph_client
from msgraph.generated.models.user import User
from msgraph.generated.models.password_profile import PasswordProfile

TENANT_ID     = os.environ.get("ARM_TENANT_ID")
CLIENT_ID     = os.environ.get("ARM_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET")
DOMAIN        = "brsankaraoutlook.onmicrosoft.com"

GROUP_MAPPING = {
    "IT":         "GRP-IT",
    "DEV":        "GRP-DEV",
    "RH":         "GRP-RH",
    "FINANCE":    "GRP-FINANCE",
    "MANAGEMENT": "GRP-MANAGEMENT"
}

async def migrate_user(client, user):
    upn = user["new_upn"]
    try:
        existing = await client.users.by_user_id(upn).get()
        if existing:
            print(f"⚠️ Déjà existant, skip création : {upn}")
            return {"upn": upn, "status": "success"}
    except Exception:
        try:
            new_user = User(
                display_name=f"{user['first_name']} {user['last_name']}",
                user_principal_name=upn,
                mail_nickname=f"{user['first_name'].lower()}.{user['last_name'].lower()}",
                department=user["department"],
                job_title=user["job_title"],
                account_enabled=True,
                password_profile=PasswordProfile(
                    password="TempMigration123!",
                    force_change_password_next_sign_in=True
                )
            )
            await client.users.post(new_user)
            print(f"✅ Migré : {upn}")
            print(f"   ⏳ Attente propagation Azure AD...")
            await asyncio.sleep(8)
            return {"upn": upn, "status": "success"}
        except Exception as e:
            print(f"❌ Erreur : {upn} → {e}")
            return {"upn": upn, "status": "failed", "error": str(e)}

async def assign_to_group(client, user_id, group_id):
    from msgraph.generated.models.reference_create import ReferenceCreate
    ref = ReferenceCreate(
        odata_id=f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"
    )
    await client.groups.by_group_id(group_id).members.ref.post(ref)

async def main():
    print("🚀 Démarrage de la migration...")

    if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Variables d'environnement manquantes !")
        return

    with open("../reports/pre_migration_report.json", "r") as f:
        analysis = json.load(f)

    client = get_graph_client(TENANT_ID, CLIENT_ID, CLIENT_SECRET)

    groups = await client.groups.get()
    group_map = {g.display_name: g.id for g in groups.value}

    migration_results = {
        "migrated": [],
        "conflicts": analysis["conflicts"],
        "disabled": analysis["disabled"],
        "failed": []
    }

    print(f"\n👥 Migration de {len(analysis['to_migrate'])} utilisateurs...")
    for user in analysis["to_migrate"]:
        result = await migrate_user(client, user)
        if result["status"] == "success":
            try:
                azure_user = await client.users.by_user_id(user["new_upn"]).get()
                group_name = GROUP_MAPPING.get(user["department"])
                if group_name and group_name in group_map:
                    await assign_to_group(client, azure_user.id, group_map[group_name])
                    print(f"   → Assigné à {group_name}")
            except Exception as e:
                print(f"   ⚠️ Erreur assignation groupe : {e}")
            migration_results["migrated"].append(user)
        else:
            migration_results["failed"].append(result)

    with open("../reports/migration_report.json", "w") as f:
        json.dump(migration_results, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Résumé migration:")
    print(f"   Migrés           : {len(migration_results['migrated'])}")
    print(f"   Conflits         : {len(migration_results['conflicts'])}")
    print(f"   Désactivés       : {len(migration_results['disabled'])}")
    print(f"   Échoués          : {len(migration_results['failed'])}")
    print(f"\n💾 Rapport sauvegardé : reports/migration_report.json")

if __name__ == "__main__":
    asyncio.run(main())