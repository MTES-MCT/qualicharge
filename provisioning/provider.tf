terraform {
  required_providers {
    metabase = {
      source = "bnjns/metabase"
      version = "0.9.1"
    }
  }
}

provider "metabase" {
  # Configured using environment variables
  # See env.d/terraform
}
