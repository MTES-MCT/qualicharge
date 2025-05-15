DELETE
FROM activity
WHERE issued_at < CURRENT_DATE - interval :clean_before ; -- FIXME: should check variable is set
