# Récupère les infos du tenant
data "azuread_client_config" "current" {}

# Crée les groupes migrés depuis l'on-premise
resource "azuread_group" "migrated_groups" {
  for_each         = toset(var.groups)
  display_name     = each.value
  description      = "Groupe migré depuis AD on-premise"
  security_enabled = true
}

# Resource Group pour les ressources de l'entreprise migrée
resource "azurerm_resource_group" "migrated_rg" {
  name     = "rg-migrated-company"
  location = "West Europe"
  tags = {
    Environment = "Production"
    Project     = "AD-Migration"
    MigratedAt  = timestamp()
  }
}

# RBAC : groupe IT → Contributor
resource "azurerm_role_assignment" "it_contributor" {
  scope                = azurerm_resource_group.migrated_rg.id
  role_definition_name = "Contributor"
  principal_id         = azuread_group.migrated_groups["GRP-IT"].object_id
}

# RBAC : groupe DEV → Contributor
resource "azurerm_role_assignment" "dev_contributor" {
  scope                = azurerm_resource_group.migrated_rg.id
  role_definition_name = "Contributor"
  principal_id         = azuread_group.migrated_groups["GRP-DEV"].object_id
}

# RBAC : groupe MANAGEMENT → Reader sur la subscription
resource "azurerm_role_assignment" "management_reader" {
  scope                = "/subscriptions/${var.subscription_id}"
  role_definition_name = "Reader"
  principal_id         = azuread_group.migrated_groups["GRP-MANAGEMENT"].object_id
}