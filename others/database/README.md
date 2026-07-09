# Database Artifacts

This folder contains the MySQL database deliverables derived from the approved ERD.

## Files

| File | Purpose |
| --- | --- |
| `schema.sql` | Main MySQL `CREATE TABLE` schema with primary keys, foreign keys, unique constraints, and indexes. |
| `seed-core.sql` | Starter seed data for roles and the root DICT organizational unit. |
| `data-dictionary.md` | Explanation of every table and field in beginner-friendly terms. |
| `psgc-import-plan.md` | Plan for importing official PSA PSGC data into local MySQL lookup tables. |

## Suggested Setup Order

1. Create the MySQL database.
2. Run `schema.sql`.
3. Run `seed-core.sql`.
4. Import PSGC data later using the process in `psgc-import-plan.md`.

Example:

```powershell
mysql -u root -p attendance_system < others\database\schema.sql
mysql -u root -p attendance_system < others\database\seed-core.sql
```

## Important Notes

* The public attendance form should save records directly to MySQL.
* PSGC data should be imported into local lookup tables instead of being called live during attendee submission.
* External attendees do not have user accounts.
* Official attendance sheet exports should normally include only `attendance_records` with `attendance_status = 'valid'`.
