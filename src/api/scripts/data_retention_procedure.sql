--
-- Configure TimescaleDB retention policy
--
-- REQUIREMENT:
-- One should set the `drop_after` variable while calling this script
--
-- psql --set=drop_after='{"drop_after":"20 days"}' "${DATABASE_URL}" -f scripts/data_retention_procedure.sql  
--
call generic_retention(config => :'drop_after');
