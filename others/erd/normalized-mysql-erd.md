# Normalized MySQL ERD Design

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This document defines the proposed MySQL database structure for the MVP. It is based on the updated DFDs and the supervisor-provided DICT attendance sheet format.

The design avoids one large attendance table. Program data, event data, admin users, assignments, attendance records, exports, and audit logs are separated so the database can satisfy at least 2NF and is designed toward 3NF.

## 2. Core Tables

The MVP database has nine core operational/admin tables:

1. `roles`
2. `organizational_units`
3. `users`
4. `programs`
5. `program_admin_assignments`
6. `events`
7. `attendance_records`
8. `attendance_sheet_exports`
9. `audit_logs`

The `organizational_units` table stores DICT offices, divisions, sections, units, or similar internal groups in one hierarchy. This is cleaner than storing a free-text office/division value directly in `programs`.

Because the supervisor mentioned PSGC codes for address handling, the database also includes normalized PSGC/address support tables:

10. `attendance_record_addresses`
11. `psgc_regions`
12. `psgc_provinces`
13. `psgc_cities_municipalities`
14. `psgc_barangays`

The address tables are separated from the official attendance sheet output. The current DICT attendance sheet template does not print address columns, but the system can still store PSGC-coded address data if the office requires address collection in the public attendance page.

## 3. Table Design

### 3.1 roles

Stores admin role definitions.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `role_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique role ID |
| `role_name` | VARCHAR(50) | UNIQUE | Example: `super_admin`, `program_admin` |
| `description` | VARCHAR(255) |  | Role description |
| `is_active` | TINYINT(1) |  | 1 active, 0 inactive |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

### 3.2 users

Stores admin login accounts. External attendees are not stored here because they do not log in.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `user_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique admin user ID |
| `role_id` | BIGINT UNSIGNED | FK -> `roles.role_id` | User role |
| `org_unit_id` | BIGINT UNSIGNED NULL | FK -> `organizational_units.org_unit_id` | Employee's assigned DICT office/division/unit, if tracked |
| `full_name` | VARCHAR(150) |  | Admin full name |
| `email` | VARCHAR(150) | UNIQUE | Login email |
| `password_hash` | VARCHAR(255) |  | Hashed password only |
| `account_status` | ENUM('active','inactive') |  | Login status |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

### 3.3 organizational_units

Stores DICT offices, divisions, sections, units, or similar organizational groups. A parent-child relationship allows the system to represent hierarchy without hardcoding separate office and division columns.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `org_unit_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique organizational unit ID |
| `parent_unit_id` | BIGINT UNSIGNED NULL | FK -> `organizational_units.org_unit_id` | Parent office/division/unit, if applicable |
| `unit_name` | VARCHAR(200) |  | Example: DICT Regional Office No. V - Bicol |
| `unit_type` | VARCHAR(50) |  | Example: office, division, section, unit, regional_office |
| `unit_code` | VARCHAR(50) NULL | UNIQUE | Optional internal DICT code, if available |
| `is_active` | TINYINT(1) |  | 1 active, 0 inactive |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

### 3.4 programs

Stores DICT programs. Events belong to programs.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `program_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique program ID |
| `owning_unit_id` | BIGINT UNSIGNED | FK -> `organizational_units.org_unit_id` | DICT organizational unit responsible for the program |
| `program_name` | VARCHAR(200) |  | Program name |
| `description` | TEXT |  | Optional description |
| `program_status` | ENUM('active','archived') |  | Program status |
| `created_by_user_id` | BIGINT UNSIGNED | FK -> `users.user_id` | Super Admin who created it |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

### 3.5 program_admin_assignments

Stores which Program Admins are assigned to which programs. This avoids storing repeated assigned program details in the `users` table.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `assignment_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique assignment ID |
| `program_id` | BIGINT UNSIGNED | FK -> `programs.program_id` | Assigned program |
| `user_id` | BIGINT UNSIGNED | FK -> `users.user_id` | Assigned Program Admin |
| `assigned_by_user_id` | BIGINT UNSIGNED | FK -> `users.user_id` | Super Admin who assigned |
| `assignment_status` | ENUM('active','revoked') |  | Current assignment status |
| `assigned_at` | DATETIME |  | Assignment timestamp |
| `revoked_at` | DATETIME NULL |  | Revocation timestamp, if any |

Recommended constraint:

* `UNIQUE(program_id, user_id)` to avoid duplicate active assignment records for the same program and admin.

### 3.6 events

Stores event details. Each event belongs to exactly one program.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `event_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique event ID |
| `program_id` | BIGINT UNSIGNED | FK -> `programs.program_id` | Parent program |
| `created_by_user_id` | BIGINT UNSIGNED | FK -> `users.user_id` | Admin who created the event |
| `event_title` | VARCHAR(200) |  | Event/seminar/meeting title |
| `event_description` | TEXT |  | Optional event description |
| `venue` | VARCHAR(255) |  | Event venue |
| `event_date` | DATE |  | Date shown on attendance sheet |
| `event_code` | VARCHAR(100) | UNIQUE | Public code/slug for link |
| `public_attendance_url` | VARCHAR(500) |  | Public attendance link |
| `qr_code_path` | VARCHAR(500) |  | Stored QR image/file path |
| `event_status` | ENUM('draft','open','closed','archived') |  | Attendance availability |
| `opened_at` | DATETIME NULL |  | When attendance opened |
| `closed_at` | DATETIME NULL |  | When attendance closed |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

### 3.7 attendance_records

Stores attendee submissions for a specific event. This is the main attendance data table.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `attendance_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique attendance record ID |
| `event_id` | BIGINT UNSIGNED | FK -> `events.event_id` | Event attended |
| `first_name` | VARCHAR(100) |  | Atomic name field |
| `middle_name` | VARCHAR(100) NULL |  | Atomic name field |
| `last_name` | VARCHAR(100) |  | Atomic name field |
| `suffix` | VARCHAR(30) NULL |  | Example: Jr., III |
| `school_university` | VARCHAR(200) |  | Template column |
| `designation_category` | VARCHAR(150) |  | Template column |
| `sex` | ENUM('F','M') |  | Template sex checkbox |
| `email` | VARCHAR(150) |  | Used for duplicate check |
| `consent_documentation_publication` | TINYINT(1) |  | Photo/video/audio and publication consent |
| `consent_database_processing` | TINYINT(1) |  | Organizer database/future processing consent |
| `signature_text` | VARCHAR(150) NULL |  | Optional typed signature |
| `signature_image_path` | VARCHAR(500) NULL |  | Optional captured signature image |
| `submitted_at` | DATETIME |  | Submission timestamp |
| `attendance_status` | ENUM('valid','duplicate','invalid','void') |  | Record status |
| `duplicate_flag` | TINYINT(1) |  | 1 if possible duplicate |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

Recommended constraint:

* `UNIQUE(event_id, email)` if email is required for every attendee.
* If email can be optional, use an index instead and handle duplicate review in application logic.

### 3.8 attendance_sheet_exports

Stores generated attendance sheet/download history. The generated file is an output; the source data remains in `events` and `attendance_records`.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `export_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique export ID |
| `event_id` | BIGINT UNSIGNED | FK -> `events.event_id` | Exported event |
| `exported_by_user_id` | BIGINT UNSIGNED | FK -> `users.user_id` | Admin who generated/downloaded |
| `export_format` | ENUM('pdf','xlsx','csv') |  | MVP likely PDF |
| `file_path` | VARCHAR(500) NULL |  | Stored generated file path, if saved |
| `total_records` | INT UNSIGNED |  | Count of included attendance records |
| `exported_at` | DATETIME |  | Export timestamp |

### 3.9 audit_logs

Stores important admin and system actions.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `audit_log_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique log ID |
| `user_id` | BIGINT UNSIGNED NULL | FK -> `users.user_id` | Nullable for public/system events |
| `action` | VARCHAR(100) |  | Example: `created_event`, `generated_qr` |
| `entity_type` | VARCHAR(100) |  | Example: `event`, `attendance_record` |
| `entity_id` | BIGINT UNSIGNED NULL |  | Affected record ID |
| `description` | VARCHAR(500) |  | Human-readable log summary |
| `old_values_json` | JSON NULL |  | Optional previous values |
| `new_values_json` | JSON NULL |  | Optional new values |
| `ip_address` | VARCHAR(45) NULL |  | IPv4/IPv6 |
| `user_agent` | VARCHAR(500) NULL |  | Optional browser/client info |
| `created_at` | DATETIME |  | Log timestamp |

### 3.10 attendance_record_addresses

Stores optional address data for a specific attendance submission using PSGC lookup codes. This keeps address data out of `attendance_records` and avoids repeated region/province/city/barangay names.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `address_id` | BIGINT UNSIGNED AUTO_INCREMENT | PK | Unique address ID |
| `attendance_id` | BIGINT UNSIGNED | FK -> `attendance_records.attendance_id` | Linked attendance submission |
| `region_code` | VARCHAR(10) | FK -> `psgc_regions.region_code` | PSGC region code |
| `province_code` | VARCHAR(10) NULL | FK -> `psgc_provinces.province_code` | Nullable for areas without province-level grouping |
| `city_municipality_code` | VARCHAR(10) | FK -> `psgc_cities_municipalities.city_municipality_code` | PSGC city/municipality code |
| `barangay_code` | VARCHAR(10) | FK -> `psgc_barangays.barangay_code` | PSGC barangay code |
| `street_address` | VARCHAR(255) NULL |  | House no., street, subdivision, purok, etc. |
| `postal_code` | VARCHAR(10) NULL |  | Optional postal code |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

Recommended constraint:

* `UNIQUE(attendance_id)` if each attendance submission should have only one address.

### 3.11 psgc_regions

Stores PSGC region lookup records.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `region_code` | VARCHAR(10) | PK | Official PSGC region code |
| `region_name` | VARCHAR(150) |  | Region name |
| `is_active` | TINYINT(1) |  | 1 active, 0 inactive |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

### 3.12 psgc_provinces

Stores PSGC province lookup records.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `province_code` | VARCHAR(10) | PK | Official PSGC province code |
| `region_code` | VARCHAR(10) | FK -> `psgc_regions.region_code` | Parent region |
| `province_name` | VARCHAR(150) |  | Province name |
| `is_active` | TINYINT(1) |  | 1 active, 0 inactive |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

### 3.13 psgc_cities_municipalities

Stores PSGC city/municipality lookup records.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `city_municipality_code` | VARCHAR(10) | PK | Official PSGC city/municipality code |
| `region_code` | VARCHAR(10) | FK -> `psgc_regions.region_code` | Parent region |
| `province_code` | VARCHAR(10) NULL | FK -> `psgc_provinces.province_code` | Nullable where applicable |
| `city_municipality_name` | VARCHAR(150) |  | City/municipality name |
| `city_municipality_type` | ENUM('city','municipality') |  | Local government type |
| `is_active` | TINYINT(1) |  | 1 active, 0 inactive |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

### 3.14 psgc_barangays

Stores PSGC barangay lookup records.

| Column | Suggested MySQL Type | Key | Notes |
| --- | --- | --- | --- |
| `barangay_code` | VARCHAR(10) | PK | Official PSGC barangay code |
| `city_municipality_code` | VARCHAR(10) | FK -> `psgc_cities_municipalities.city_municipality_code` | Parent city/municipality |
| `barangay_name` | VARCHAR(150) |  | Barangay name |
| `is_active` | TINYINT(1) |  | 1 active, 0 inactive |
| `created_at` | DATETIME |  | Creation timestamp |
| `updated_at` | DATETIME |  | Last update timestamp |

## 4. Main Relationships

* One `role` can be assigned to many `users`.
* One `organizational_unit` can contain many child `organizational_units`.
* One `organizational_unit` can be assigned to many `users`.
* One `organizational_unit` can own or handle many `programs`.
* One `user` can create many `programs`.
* One `program` can have many `program_admin_assignments`.
* One `user` can have many `program_admin_assignments`.
* One `program` can have many `events`.
* One `user` can create many `events`.
* One `event` can have many `attendance_records`.
* One `event` can have many `attendance_sheet_exports`.
* One `user` can generate many `attendance_sheet_exports`.
* One `user` can have many `audit_logs`.
* One `attendance_record` can have zero or one `attendance_record_addresses` row.
* One `psgc_region` can have many `psgc_provinces`.
* One `psgc_region` can have many `psgc_cities_municipalities`.
* One `psgc_province` can have many `psgc_cities_municipalities`.
* One `psgc_city_municipality` can have many `psgc_barangays`.
* One PSGC lookup row can be referenced by many attendance record addresses.

## 5. DICT Attendance Sheet Field Mapping

The supervisor-provided template is an output format. It is not imported as a database table.

### Header Fields

| Attendance Sheet Field | Source Table/Column | Notes |
| --- | --- | --- |
| Title of Event/Seminar/Meeting | `events.event_title` | Printed in sheet header |
| Venue | `events.venue` | Printed in sheet header |
| Date | `events.event_date` | Printed in sheet header |
| Office heading | `organizational_units.unit_name` through `programs.owning_unit_id` | Example: DICT Regional Office No. V - Bicol |
| Privacy notice | Fixed application text | Not a per-event imported template |

### Attendance Table Fields

| Attendance Sheet Column | Source Table/Column | Notes |
| --- | --- | --- |
| Row number | Generated during export | Not stored |
| Name | Combined from `first_name`, `middle_name`, `last_name`, `suffix` | Stored separately for normalization |
| School/University | `attendance_records.school_university` | Direct mapping |
| Designation/Category | `attendance_records.designation_category` | Direct mapping |
| Sex F/M | `attendance_records.sex` | Rendered as checked F or M |
| Email Address | `attendance_records.email` | Direct mapping |
| Consent for documentation/publication | `attendance_records.consent_documentation_publication` | Rendered as checked if yes |
| Consent for organizer database/future processing | `attendance_records.consent_database_processing` | Rendered as checked if yes |
| Signature | `signature_text` or `signature_image_path` | Optional depending on office decision |

### Address Fields

Address fields are not shown in the current supervisor-provided attendance sheet template. If the public attendance page collects address data, it should be stored in `attendance_record_addresses` using PSGC codes and should not be printed in the official attendance sheet unless the office later changes the template.

## 6. Normalization Explanation

### 6.1 First Normal Form

The design uses atomic fields:

* Names are stored as `first_name`, `middle_name`, `last_name`, and `suffix`.
* One attendance submission is one row in `attendance_records`.
* One event is one row in `events`.
* Repeating groups, such as multiple Program Admin assignments, are stored in `program_admin_assignments`.
* Address parts are stored as PSGC codes, not as repeated free-text region/province/city/barangay names.

### 6.2 Second Normal Form

The design avoids partial dependency by keeping each table focused on one entity or relationship:

* Program fields are stored only in `programs`.
* Organizational unit names and hierarchy are stored only in `organizational_units`.
* Event fields are stored only in `events`.
* Attendance submission fields are stored only in `attendance_records`.
* Attendance address fields are stored only in `attendance_record_addresses`.
* Program Admin assignment data is stored in its own junction table.

Most tables use single-column primary keys. The important business uniqueness rules, such as `UNIQUE(program_id, user_id)` and possible `UNIQUE(event_id, email)`, are handled as separate constraints.

### 6.3 Third Normal Form

The design avoids transitive dependency:

* `attendance_records` does not repeat program name, event title, venue, or event date. It stores only `event_id`.
* `events` does not repeat Program Admin names or emails. It stores `created_by_user_id`.
* `programs` does not repeat office/division/unit names. It stores `owning_unit_id`.
* `users` does not repeat office/division/unit names. It stores `org_unit_id` when employee assignment is tracked.
* `program_admin_assignments` does not repeat user or program details. It stores foreign keys.
* `attendance_sheet_exports` does not duplicate attendance rows. It stores export metadata only.
* `audit_logs` stores action metadata and references the admin user when applicable.
* `attendance_record_addresses` does not repeat PSGC names. It stores only PSGC code foreign keys and street-level details.
* PSGC region, province, city/municipality, and barangay names are stored only in their lookup tables.

This means updates happen in one place. For example, if an event venue is corrected, it is corrected in `events`, not in every attendance row.

## 7. Why There Is No attendees Table in the MVP

A separate `attendees` master table is not included in the MVP because external attendees do not have accounts and the system does not yet perform cross-event identity matching.

For the MVP, each attendance record is treated as an official submission for one event. If the office later wants repeat-attendee tracking or attendee profiles, an `attendees` table can be added in Phase 2.

## 8. Recommended Next Step After ERD Approval

After this ERD is approved, create the MySQL SQL schema with:

* `CREATE TABLE` statements
* Primary keys
* Foreign keys
* Unique constraints
* Indexes for common lookups, especially:
  * `users.email`
  * `users.org_unit_id`
  * `organizational_units.parent_unit_id`
  * `organizational_units.unit_code`
  * `programs.owning_unit_id`
  * `program_admin_assignments(program_id, user_id)`
  * `events.program_id`
  * `events.event_code`
  * `attendance_records.event_id`
  * `attendance_records(event_id, email)`
  * `attendance_sheet_exports.event_id`
  * `audit_logs.user_id`
  * `audit_logs.created_at`
  * `attendance_record_addresses.attendance_id`
  * `attendance_record_addresses.region_code`
  * `attendance_record_addresses.province_code`
  * `attendance_record_addresses.city_municipality_code`
  * `attendance_record_addresses.barangay_code`
  * `psgc_provinces.region_code`
  * `psgc_cities_municipalities.region_code`
  * `psgc_cities_municipalities.province_code`
  * `psgc_barangays.city_municipality_code`
