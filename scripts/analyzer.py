import json
import asyncio
import os
from graph_client import get_graph_client

TENANT_ID     = os.environ.get("ARM_TENANT_ID")
CLIENT_ID     = os.environ.get("ARM_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET")
DOMAIN        = "brsankaraoutlook.onmicrosoft.com"

async def analyze(on_premise_data):
    print("🔍 Analyse pre-migration...")
    client = get_graph_client(TENANT_ID, CLIENT_ID, CLIENT_SECRET)

    # Récupère les users existants dans Azure AD
    existing_users = await client.users.get()
    existing_upns = [u.user_principal_name.lower() for u in existing_users.value]

    results = {
        "total_users": len(on_premise_data["users"]),
        "to_migrate": [],
        "conflicts": [],
        "disabled": [],
        "groups": on_premise_data["groups"]
    }

    for user in on_premise_data["users"]:
        new_upn = f"{user['first_name'].lower()}.{user['last_name'].lower()}@{DOMAIN}"

        if not user["enabled"]:
            results["disabled"].append({**user, "new_upn": new_upn})
            print(f"⏭️  Désactivé, skip : {user['username']}")
        elif new_upn.lower() in existing_upns:
            results["conflicts"].append({**user, "new_upn": new_upn})
            print(f"⚠️  Conflit détecté : {new_upn}")
        else:
            results["to_migrate"].append({**user, "new_upn": new_upn})
            print(f"✅ À migrer : {new_upn}")

    print(f"\n📊 Résumé pre-migration:")
    print(f"   Total users      : {results['total_users']}")
    print(f"   À migrer         : {len(results['to_migrate'])}")
    print(f"   Conflits         : {len(results['conflicts'])}")
    print(f"   Désactivés       : {len(results['disabled'])}")

    return results

async def main():
    with open("../data/on_premise_ad.json", "r") as f:
        on_premise_data = json.load(f)
    
    results = await analyze(on_premise_data)
    
    # Sauvegarde le rapport d'analyse
    import json as json_module
    with open("../reports/pre_migration_report.json", "w") as f:
        json_module.dump(results, f, indent=2, ensure_ascii=False)
    print("\n💾 Rapport sauvegardé : reports/pre_migration_report.json")

if __name__ == "__main__":
    asyncio.run(main())