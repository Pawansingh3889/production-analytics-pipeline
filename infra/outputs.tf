output "api_url" {
  value = "http://localhost:${docker_container.api.ports[0].external}"
}

output "sandbox_port" {
  value = docker_container.erp_sandbox.ports[0].external
}
