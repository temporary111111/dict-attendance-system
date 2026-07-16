# PSGC Import Plan

## Purpose

The system stores PSGC data locally in MySQL so the attendance form can use reliable address dropdowns without depending on a live external API during events.

Official PSA references:

* PSGC masterlist/download page: https://psa.gov.ph/classification/psgc
* PSA PSGC API documentation: https://psa.gov.ph/classifications-api/psgc
* PSA Classifications API access guide: https://psa.gov.ph/classifications-api/access-guide

## Recommended Approach

Use a local import/sync process:

1. Download the latest PSGC masterlist from the PSA PSGC page.
2. Import the file into staging tables or a temporary processing script.
3. Transform the official rows into the local normalized lookup tables:
   * `psgc_regions`
   * `psgc_provinces`
   * `psgc_cities_municipalities`
   * `psgc_barangays`
4. Mark current rows as active.
5. Keep older referenced rows inactive instead of deleting them.
6. The attendance form reads from the local MySQL tables only.

This avoids a failure mode where attendees cannot submit attendance because the PSA API or network connection is unavailable.

## Current System Workflow

The Super Admin has an in-app import flow for the official PSA `.xlsx` masterlist:

1. Download the official PSGC Excel masterlist from PSA.
2. In `PSGC Data`, select the file and enter its PSA release/version.
3. Use `Preview file`. The system reads the workbook without writing to MySQL.
4. The preview checks the required headers, numeric PSGC codes, duplicate codes, supported geographic levels, and the region -> province -> city/municipality -> barangay hierarchy.
5. Only a valid preview enables `Import masterlist`. The confirmation action re-validates the same uploaded file and saves all rows in one database transaction.

The import upserts regions first, then provinces, cities/municipalities, and barangays. It reactivates imported rows and records one `imported_psgc_masterlist` audit log with the file name, SHA-256 checksum, PSA release/version, and row counts.

The official PSA workbook can contain `SubMun` rows and rare blank-level grouping rows. These are valid PSA structural rows, but they are not a fifth address level in this system. The importer uses them only to resolve each affected barangay back to its parent city or municipality, then stores only the normalized four lookup levels.

The importer follows the PSA Revision 1 10-digit coding structure for normal rows: 2 digits for region, 3 digits for province/HUC, 2 digits for city/municipality, and 3 digits for barangay. This is important when resolving city-to-province foreign keys; the old 9-digit coding layout must not be used.

For safety, the current importer does not automatically deactivate rows that are absent from an uploaded file. It also never deletes old PSGC rows, so historical attendance addresses remain valid. A separate, explicitly confirmed reconciliation feature can be added later if DICT needs retirement handling for a complete masterlist.

## Why Not Live API Calls in the Public Attendance Form

The public attendance page should not call the PSA API every time an attendee selects an address because:

* Event venues may have weak internet.
* API tokens or rate limits can interrupt submissions.
* Dropdowns should be fast.
* Local tables give consistent options for the entire event.
* Old attendance records can still reference old PSGC codes.

The PSA API can still be useful for a scheduled admin-side sync tool, but it should not be a runtime dependency of attendance submission.

## Local Table Mapping

### `psgc_regions`

| Local Column | Source Meaning |
| --- | --- |
| `region_code` | Official PSGC region code |
| `region_name` | Region name |
| `is_active` | 1 if present in latest imported PSGC set |

### `psgc_provinces`

| Local Column | Source Meaning |
| --- | --- |
| `province_code` | Official PSGC province code |
| `region_code` | Parent region code |
| `province_name` | Province name |
| `is_active` | 1 if present in latest imported PSGC set |

### `psgc_cities_municipalities`

| Local Column | Source Meaning |
| --- | --- |
| `city_municipality_code` | Official PSGC city/municipality code |
| `region_code` | Parent region code |
| `province_code` | Parent province code, nullable if not applicable |
| `city_municipality_name` | City or municipality name |
| `city_municipality_type` | `city` or `municipality` |
| `is_active` | 1 if present in latest imported PSGC set |

### `psgc_barangays`

| Local Column | Source Meaning |
| --- | --- |
| `barangay_code` | Official PSGC barangay code |
| `city_municipality_code` | Parent city/municipality code |
| `barangay_name` | Barangay name |
| `is_active` | 1 if present in latest imported PSGC set |

## Suggested Import Workflow

### 1. Keep a raw copy

Keep the downloaded source file in a controlled folder outside the deployed application, for example:

```text
storage/imports/psgc/PSGC-latest.xlsx
```

Also record:

```text
source_url
downloaded_at
source_period_or_version
imported_by
```

The current ERD does not include an `import_batches` table because it is not required for MVP, but it can be added later if the office wants detailed import audit history.

### 2. Load to staging

Use a staging table or a script to read the PSA file first. Avoid importing directly into final tables without validation.

Example staging idea:

```sql
CREATE TABLE psgc_staging_raw (
  psgc_code VARCHAR(20),
  geographic_name VARCHAR(255),
  geographic_level VARCHAR(50),
  region_code VARCHAR(10),
  province_code VARCHAR(10),
  city_municipality_code VARCHAR(10),
  barangay_code VARCHAR(10)
);
```

The exact staging columns may change depending on the downloaded PSA file format. The final tables should remain stable.

### 3. Validate before upsert

Check for:

* Missing PSGC codes
* Duplicate codes in the same geographic level
* Provinces with missing parent region
* Cities/municipalities with missing parent region
* Cities/municipalities with missing parent province where province is required
* Barangays with missing parent city/municipality

### 4. Retire old rows only through an explicit future reconciliation

Do not run the following directly as part of the current admin import. A future reconciliation flow must first verify that the uploaded file is a complete official masterlist and must show the affected row count to the Super Admin:

```sql
UPDATE psgc_barangays SET is_active = 0;
UPDATE psgc_cities_municipalities SET is_active = 0;
UPDATE psgc_provinces SET is_active = 0;
UPDATE psgc_regions SET is_active = 0;
```

Do not delete old rows because old attendance records may still reference them.

### 5. Upsert latest rows

Insert or update current rows in parent-to-child order:

1. Regions
2. Provinces
3. Cities/municipalities
4. Barangays

Example pattern:

```sql
INSERT INTO psgc_regions (
  region_code,
  region_name,
  is_active
)
VALUES (?, ?, 1)
ON DUPLICATE KEY UPDATE
  region_name = VALUES(region_name),
  is_active = 1,
  updated_at = CURRENT_TIMESTAMP;
```

Use the same pattern for provinces, cities/municipalities, and barangays.

## Attendance Form Dropdown Flow

The public attendance page should query only active rows:

```sql
SELECT region_code, region_name
FROM psgc_regions
WHERE is_active = 1
ORDER BY region_name;
```

After the attendee selects a region:

```sql
SELECT province_code, province_name
FROM psgc_provinces
WHERE region_code = ?
  AND is_active = 1
ORDER BY province_name;
```

After the attendee selects a province or region:

```sql
SELECT city_municipality_code, city_municipality_name, city_municipality_type
FROM psgc_cities_municipalities
WHERE region_code = ?
  AND (province_code = ? OR province_code IS NULL)
  AND is_active = 1
ORDER BY city_municipality_name;
```

After the attendee selects a city/municipality:

```sql
SELECT barangay_code, barangay_name
FROM psgc_barangays
WHERE city_municipality_code = ?
  AND is_active = 1
ORDER BY barangay_name;
```

## Storage Rule

When saving attendance address data:

* Store PSGC codes in `attendance_record_addresses`.
* Do not repeat region/province/city/barangay names in the attendance address table.
* Join with PSGC lookup tables only when displaying or exporting address details.

Example:

```text
attendance_record_addresses.region_code
attendance_record_addresses.province_code
attendance_record_addresses.city_municipality_code
attendance_record_addresses.barangay_code
```

## Future Improvement

The current importer records a summary in `audit_logs`. If DICT later needs a searchable import history with file retention and rollback metadata, add a table such as:

```text
psgc_import_batches
- import_batch_id
- source_url
- source_period
- file_name
- imported_by_user_id
- imported_at
- status
- notes
```

This is not required for MVP, but it would improve auditability.
