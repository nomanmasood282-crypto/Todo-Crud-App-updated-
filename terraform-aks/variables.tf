variable "location" {
  description = "Azure region. Central India is blocked for this free trial; South India works."
  type        = string
  default     = "southindia"
}

variable "node_vm_size" {
  description = "VM size of the node. Must be open to the subscription in the chosen region."
  type        = string
  default     = "Standard_D2as_v5" # 2 vCPU / 8 GB
}

variable "node_count" {
  description = "Number of nodes. The trial quota is 4 vCPUs per region, so at most 2 nodes of 2 vCPU."
  type        = number
  default     = 1
}

variable "os_disk_size_gb" {
  description = "OS disk size per node (smaller than the 128 GB default = a little cheaper)."
  type        = number
  default     = 64
}

variable "budget_amount" {
  description = "Budget in USD that the alerts are measured against."
  type        = number
  default     = 150
}

variable "budget_start_date" {
  description = "Start of the budget period. Must be the first day of a month (RFC3339)."
  type        = string
  default     = "2026-11-01T00:00:00Z"
}

variable "alert_email" {
  description = "Email address that receives the budget alerts. Set it in terraform.tfvars (git-ignored)."
  type        = string
}
