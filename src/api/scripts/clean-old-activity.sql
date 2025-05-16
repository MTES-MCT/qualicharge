DELETE
FROM activity
WHERE issued_at < CURRENT_DATE - INTERVAL :clean_before ; -- FIXME: should check variable is set
VACUUM (FULL, ANALYZE) activity; -- FIXME: VACUUM locks the table / db ?
