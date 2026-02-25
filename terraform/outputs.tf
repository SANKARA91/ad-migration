output "migrated_groups" {
  description = "Groupes Azure AD créés"
  value       = { for k, v in azuread_group.migrated_groups : k => v.object_id }
}

output "resource_group_id" {
  description = "Resource Group créé pour l'entreprise migrée"
  value       = azurerm_resource_group.migrated_rg.id
}