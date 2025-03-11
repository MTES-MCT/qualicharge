# Database
resource "metabase_database" "qualicharge" {
  engine = "postgres"
  name   = "QualiCharge API"

  details = jsonencode({
    host   = "postgresql"
    port   = 5432
    dbname = "qualicharge-api"
    user   = "qualicharge"
  })
  details_secure = jsonencode({
    password = "pass"
  })
}

resource "metabase_database" "indicators" {
  engine = "postgres"
  name   = "QualiCharge Indicators"

  details = jsonencode({
    host   = "postgresql"
    port   = 5432
    dbname = "qualicharge-indicators"
    user   = "qualicharge"
  })
  details_secure = jsonencode({
    password = "pass"
  })
}