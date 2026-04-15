terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# SQL Server sandbox
resource "docker_image" "mssql" {
  name = "mcr.microsoft.com/mssql/server:2022-latest"
}

resource "docker_container" "erp_sandbox" {
  name  = "erp_sandbox"
  image = docker_image.mssql.image_id

  env = [
    "ACCEPT_EULA=Y",
    "SA_PASSWORD=DemoPass123!",
    "MSSQL_PID=Developer"
  ]

  ports {
    internal = 1433
    external = 1433
  }

  restart = "unless-stopped"
}

# Production DuckDB/SQLite warehouse (volume)
resource "docker_volume" "warehouse_data" {
  name = "production_warehouse"
}

# FastAPI application
resource "docker_image" "api" {
  name = "production-api:latest"
  build {
    context = ".."
    dockerfile = "infra/Dockerfile.api"
  }
}

resource "docker_container" "api" {
  name  = "production_api"
  image = docker_image.api.image_id

  ports {
    internal = 8000
    external = 8000
  }

  env = [
    "SOURCE_DB=mssql+pyodbc://pipeline_reader:ReadOnly123!@erp_sandbox/production_dw?driver=ODBC+Driver+17+for+SQL+Server",
    "TARGET_DB=sqlite:///data/production_dw.db"
  ]

  volumes {
    volume_name    = docker_volume.warehouse_data.name
    container_path = "/app/data"
  }

  depends_on = [docker_container.erp_sandbox]
  restart    = "unless-stopped"
}
