# ERD Notes

This folder contains the normalized MySQL database design for the DICT Program and Event Attendance Monitoring and Reporting System.

The database design follows the current MVP direction:

* MySQL database
* At least 2NF, designed toward 3NF
* No Google Forms tables
* No form-builder tables
* Fixed attendance fields based on the DICT attendance sheet format
* DICT office/division/unit hierarchy modeled through `organizational_units`
* PSGC-coded address support in separate normalized lookup/address tables
* Downloadable attendance sheet generated from stored event and attendance records

## Main Files

* `normalized-mysql-erd.md` - table design, relationships, normalization explanation, and DICT attendance sheet field mapping
* `source/attendance-system-erd.mmd` - Mermaid ERD source
* `attendance-system-erd.png` - generated ERD image for reports/presentations
* `attendance-system-erd.svg` - generated vector ERD
* `source/attendance-system-erd.drawio` - editable diagrams.net / draw.io ERD

## Regeneration

Regenerate the Mermaid PNG/SVG:

```powershell
python others\erd\source\render_erd_diagram.py
```

Regenerate the editable Draw.io ERD:

```powershell
python others\erd\source\render_erd_drawio.py
```

## Important Design Decision

External attendees do not have user accounts in the MVP. Their submitted attendance details are stored per event in `attendance_records`. DICT office/division/unit data is stored in `organizational_units`, then referenced by `programs.owning_unit_id` and optionally by `users.org_unit_id`. PSGC-coded address details, if collected, are stored separately in `attendance_record_addresses` and linked to PSGC lookup tables. A separate `attendees` master table is intentionally not included yet because cross-event attendee identity matching is out of scope for the MVP.

## SQL Implementation

The MySQL schema and database supporting documents are in `others/database/`:

* `schema.sql`
* `seed-core.sql`
* `data-dictionary.md`
* `psgc-import-plan.md`
