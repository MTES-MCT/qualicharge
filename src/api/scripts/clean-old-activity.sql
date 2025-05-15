-- 
-- Clean old entries from the activity table
-- 
-- REQUIREMENT:
-- One should set the `clean_older_than` variable while calling this script
--
-- psql --set=clean_older_than='1 month' "${DATABASE_URL}" -f scripts/clean-old-activity.sql
-- 
DELETE
FROM activity
WHERE issued_at < CURRENT_DATE - INTERVAL :'clean_older_than'; -- 
VACUUM (VERBOSE, ANALYZE) activity;
