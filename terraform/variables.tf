variable "tenant_id" {
  type      = string
  sensitive = true
}

variable "client_id" {
  type      = string
  sensitive = true
}

variable "client_secret" {
  type      = string
  sensitive = true
}

variable "subscription_id" {
  type      = string
  sensitive = true
}

variable "company_name" {
  type    = string
  default = "migrated"
}

variable "groups" {
  description = "Groupes à créer dans Azure AD"
  type        = list(string)
  default = [
    "GRP-IT",
    "GRP-DEV",
    "GRP-RH",
    "GRP-FINANCE",
    "GRP-MANAGEMENT"
  ]
}