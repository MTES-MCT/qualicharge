terraform {
  required_providers {
    metabase = {
      source = "bnjns/metabase"
      version = "0.10.0"
    }
  }
}

provider "metabase" {
  # Configured using environment variables
  # See env.d/terraform
}
