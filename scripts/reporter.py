import json
import os
from datetime import datetime

def generate_report():
    print("📝 Génération du rapport final...")

    with open("../reports/pre_migration_report.json", "r") as f:
        pre = json.load(f)

    with open("../reports/migration_report.json", "r") as f:
        migration = json.load(f)

    report = f"""
╔══════════════════════════════════════════════════════════════╗
║           RAPPORT DE MIGRATION AD ON-PREMISE → AZURE AD      ║
╚══════════════════════════════════════════════════════════════╝

📅 Date        : {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
🏢 Source      : OldCorp (AD On-Premise)
☁️  Destination : Azure AD / Microsoft Entra ID

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RÉSUMÉ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total users on-premise  : {pre['total_users']}
  ✅ Migrés avec succès   : {len(migration['migrated'])}
  ⚠️  Conflits détectés   : {len(migration['conflicts'])}
  ⏭️  Désactivés skippés  : {len(migration['disabled'])}
  ❌ Échecs               : {len(migration['failed'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ UTILISATEURS MIGRÉS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    for user in migration["migrated"]:
        report += f"\n  • {user['first_name']} {user['last_name']} ({user['department']}) → {user['new_upn']}"

    report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  CONFLITS DÉTECTÉS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    if migration["conflicts"]:
        for user in migration["conflicts"]:
            report += f"\n  • {user['first_name']} {user['last_name']} → {user['new_upn']} (compte existant)"
    else:
        report += "\n  Aucun conflit détecté"

    report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏭️  COMPTES DÉSACTIVÉS (NON MIGRÉS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    if migration["disabled"]:
        for user in migration["disabled"]:
            report += f"\n  • {user['username']} (désactivé dans l'AD source)"
    else:
        report += "\n  Aucun compte désactivé"

    report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ ÉCHECS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    if migration["failed"]:
        for user in migration["failed"]:
            report += f"\n  • {user['upn']} → {user.get('error', 'Erreur inconnue')}"
    else:
        report += "\n  Aucun échec ✅"

    report += "\n\n══════════════════════════════════════════════════════════════\n"

    print(report)

    # Sauvegarde le rapport texte
    with open("../reports/final_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("💾 Rapport sauvegardé : reports/final_report.txt")

if __name__ == "__main__":
    generate_report()