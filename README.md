# 🏢 AD On-Premise → Azure AD Migration

Automatisation complète de la migration d'un Active Directory on-premise vers Azure AD / Microsoft Entra ID, avec détection des conflits, rapport détaillé et pipeline CI/CD.

## 📋 Description

Ce projet simule une migration réelle d'entreprise :
- Un AD on-premise est simulé via un fichier JSON
- Le pipeline analyse, migre et génère un rapport automatiquement
- Les conflits sont détectés et gérés avant la migration
- Tout est automatisé via GitHub Actions

## 🏗️ Architecture
```
AD On-Premise (JSON)
        ↓
   analyzer.py        ← Détecte les conflits
        ↓
   migrator.py        ← Migre les users via Graph API
        ↓
   reporter.py        ← Génère le rapport final
        ↓
   Azure AD / Entra ID
        ↑
   Terraform          ← Crée les groupes et RBAC
```

## 🛠️ Stack technique

| Outil | Usage |
|-------|-------|
| Terraform | Création des groupes AD et RBAC Azure |
| Python | Scripts d'analyse, migration et reporting |
| Microsoft Graph API | Interaction avec Azure AD |
| GitHub Actions | Pipeline CI/CD automatisé |
| Azure AD / Entra ID | Destination de la migration |

## 📁 Structure du projet
```
ad-migration/
├── .github/
│   └── workflows/
│       └── migration.yml      # Pipeline CI/CD
├── data/
│   ├── on_premise_ad.json     # AD on-premise simulé
│   └── migration_config.yml   # Config de la migration
├── scripts/
│   ├── graph_client.py        # Connexion Microsoft Graph API
│   ├── analyzer.py            # Analyse pre-migration
│   ├── migrator.py            # Migration des utilisateurs
│   └── reporter.py            # Génération du rapport
├── terraform/
│   ├── main.tf                # Groupes AD et RBAC
│   ├── variables.tf
│   ├── outputs.tf
│   └── providers.tf
└── README.md
```

## ⚙️ Fonctionnement

### Étape 1 : Analyse pre-migration
- Lit les utilisateurs depuis `on_premise_ad.json`
- Compare avec les users existants dans Azure AD
- Détecte les conflits (UPN déjà existant)
- Identifie les comptes désactivés à ne pas migrer
- Génère `reports/pre_migration_report.json`

### Étape 2 : Migration
- Crée les comptes manquants dans Azure AD
- Skips les users déjà existants (gestion des conflits)
- Assigne chaque user à son groupe de département
- Génère `reports/migration_report.json`

### Étape 3 : Rapport final
- Synthèse complète de la migration
- Liste des users migrés, en conflit, désactivés, échoués
- Export en `reports/final_report.txt`

## 🚀 Déploiement

### Prérequis
- Terraform >= 1.0
- Python >= 3.11
- Azure CLI
- Un tenant Azure AD

### 1. Configurer l'App Registration Azure
- Créer une App Registration dans Azure AD
- Ajouter les permissions Graph API : `User.ReadWrite.All`, `Group.ReadWrite.All`, `Directory.ReadWrite.All`
- Accorder le consentement administrateur

### 2. Déployer l'infrastructure Terraform
```bash
cd terraform
terraform init
terraform apply
```

### 3. Configurer les secrets GitHub
Ajouter dans Settings → Secrets → Actions :
- `ARM_TENANT_ID`
- `ARM_CLIENT_ID`
- `ARM_CLIENT_SECRET`

### 4. Lancer la migration
Modifier `data/on_premise_ad.json` et pusher sur main, ou déclencher manuellement via GitHub Actions.

## 📝 Format de l'AD on-premise simulé
```json
{
  "company": "OldCorp",
  "domain": "oldcorp.local",
  "users": [
    {
      "username": "j.dupont",
      "first_name": "Jean",
      "last_name": "Dupont",
      "department": "IT",
      "job_title": "SysAdmin",
      "enabled": true
    }
  ],
  "groups": [
    {"name": "IT", "members": ["j.dupont"]}
  ]
}
```

## 📊 Exemple de rapport généré
```
╔══════════════════════════════════════════════════════════════╗
║        RAPPORT DE MIGRATION AD ON-PREMISE → AZURE AD         ║
╚══════════════════════════════════════════════════════════════╝
📅 Date        : 25/02/2026
🏢 Source      : OldCorp (AD On-Premise)
☁️  Destination : Azure AD / Microsoft Entra ID

📊 RÉSUMÉ
  Total users on-premise  : 7
  ✅ Migrés avec succès   : 5
  ⚠️  Conflits détectés   : 1
  ⏭️  Désactivés skippés  : 1
  ❌ Échecs               : 0
```

## 🔒 Sécurité
- Secrets stockés dans GitHub Secrets
- Aucune credential dans le code source
- Principe du moindre privilège via RBAC Azure
- Comptes désactivés non migrés automatiquement