variable "name" {
  description = "Globally unique Azure Storage Account name."
  type        = string
}
variable "resource_group_name" {
  description = "Existing Azure Resource Group."
  type        = string
}
variable "location" {
  description = "Azure region."
  type        = string
}
variable "environment" {
  description = "Environment name."
  type        = string
  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "environment must be dev, qa or prod."
  }
}
variable "account_tier" {
  type    = string
  default = "Standard"
}
variable "account_replication_type" {
  type    = string
  default = "LRS"
  validation {
    condition     = contains(["LRS", "GRS", "RAGRS", "ZRS"], var.account_replication_type)
    error_message = "Use LRS, GRS, RAGRS or ZRS."
  }
}
variable "min_tls_version" {
  type    = string
  default = "TLS1_2"
}
variable "https_traffic_only_enabled" {
  type    = bool
  default = true
}
variable "tags" {
  type    = map(string)
  default = {}
}
