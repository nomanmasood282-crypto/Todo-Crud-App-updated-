output "resource_group_name" {
  value = azurerm_resource_group.aks.name
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.todo.name
}

output "get_credentials_command" {
  description = "Run this to add the cluster to your kubeconfig"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.aks.name} --name ${azurerm_kubernetes_cluster.todo.name}"
}
