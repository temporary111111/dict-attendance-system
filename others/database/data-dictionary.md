# Database Data Dictionary

## Program and Event Attendance Monitoring and Reporting System for DICT

This data dictionary explains the tables in `schema.sql`. It is written for implementation and presentation, so the focus is on what each table stores and why it exists.

## Table Summary

| Table | Purpose |
| --- | --- |
| `roles` | Stores admin role definitions such as Super Admin and Program Admin. |
| `organizational_units` | Stores DICT offices, divisions, sections, units, or similar organizational groups. |
| `users` | Stores admin login accounts. External attendees are not stored here. |
| `programs` | Stores DICT programs such as Free Wi-Fi for All, eGov Super App, or National Broadband Plan. |
| `program_admin_assignments` | Stores which Program Admin user is assigned to which program. |
| `events` | Stores specific activities/events under programs. |
| `attendance_records` | Stores submitted attendance details per event. |
| `attendance_record_addresses` | Stores optional PSGC-coded address details per attendance record. |
| `attendance_sheet_exports` | Stores generated/downloaded attendance sheet history. |
| `audit_logs` | Stores important system and admin actions. |
| `psgc_regions` | PSGC region lookup table. |
| `psgc_provinces` | PSGC province lookup table. |
| `psgc_cities_municipalities` | PSGC city/municipality lookup table. |
| `psgc_barangays` | PSGC barangay lookup table. |

## `roles`

Stores system role definitions.

| Column | Meaning |
| --- | --- |
| `role_id` | Unique role ID. |
| `role_name` | Role key, such as `super_admin` or `program_admin`. |
| `description` | Short explanation of the role. |
| `is_active` | Controls whether the role is still usable. |
| `created_at` | When the role was created. |
| `updated_at` | When the role was last updated. |

## `organizational_units`

Stores DICT organization structure in a flexible hierarchy. This avoids hardcoding separate `office` and `division` fields.

| Column | Meaning |
| --- | --- |
| `org_unit_id` | Unique organizational unit ID. |
| `parent_unit_id` | Parent unit ID. Example: a division can belong to a regional office. |
| `unit_name` | Name of the office, division, section, unit, or similar group. |
| `unit_type` | Type of unit, such as `department`, `regional_office`, `division`, `section`, or `unit`. |
| `unit_code` | Optional internal code, if DICT uses one. |
| `is_active` | Controls whether the unit is still selectable. |
| `created_at` | When the unit was created. |
| `updated_at` | When the unit was last updated. |

## `users`

Stores admin accounts that can log in. Attendees are not stored here because they use the public attendance page without login.

| Column | Meaning |
| --- | --- |
| `user_id` | Unique admin user ID. |
| `role_id` | User role. References `roles.role_id`. |
| `org_unit_id` | Employee's assigned DICT unit, if tracked. References `organizational_units.org_unit_id`. |
| `full_name` | Full name of the admin user. |
| `email` | Login email. Must be unique. |
| `password_hash` | Hashed password only. Plain passwords must never be stored. |
| `account_status` | `active` or `inactive`. |
| `created_at` | When the user was created. |
| `updated_at` | When the user was last updated. |

## `programs`

Stores DICT programs. A program is a parent initiative/category; it is not the same as an event.

Examples:

* Free Wi-Fi for All
* eGov Super App
* National Broadband Plan

| Column | Meaning |
| --- | --- |
| `program_id` | Unique program ID. |
| `owning_unit_id` | DICT unit responsible for the program. References `organizational_units.org_unit_id`. |
| `created_by_user_id` | Admin who created the program. References `users.user_id`. |
| `program_name` | Program name. |
| `description` | Optional program description. |
| `program_status` | `active` or `archived`. |
| `created_at` | When the program was created. |
| `updated_at` | When the program was last updated. |

## `program_admin_assignments`

Stores Program Admin access to programs.

| Column | Meaning |
| --- | --- |
| `assignment_id` | Unique assignment ID. |
| `program_id` | Program assigned to the admin. References `programs.program_id`. |
| `user_id` | Program Admin user. References `users.user_id`. |
| `assigned_by_user_id` | Super Admin who made the assignment. References `users.user_id`. |
| `assignment_status` | `active` or `revoked`. |
| `assigned_at` | When the assignment was made. |
| `revoked_at` | When the assignment was revoked, if applicable. |

## `events`

Stores specific events or activities under programs.

| Column | Meaning |
| --- | --- |
| `event_id` | Unique event ID. |
| `program_id` | Parent program. References `programs.program_id`. |
| `created_by_user_id` | Admin who created the event. References `users.user_id`. |
| `event_title` | Event/seminar/meeting title. |
| `event_description` | Optional event description. |
| `venue` | Event venue. |
| `event_date` | Event date shown on reports and attendance sheets. |
| `event_code` | Unique public code/slug for the attendance link. |
| `public_attendance_url` | Public attendance URL. Nullable while event is still being drafted. |
| `qr_code_path` | Stored QR image path, if the QR code is saved. |
| `event_status` | `draft`, `open`, `closed`, or `archived`. |
| `opened_at` | When attendance collection was opened. |
| `closed_at` | When attendance collection was closed. |
| `created_at` | When the event was created. |
| `updated_at` | When the event was last updated. |

## `attendance_records`

Stores one attendance submission for one event.

| Column | Meaning |
| --- | --- |
| `attendance_id` | Unique attendance record ID. |
| `event_id` | Event attended. References `events.event_id`. |
| `first_name` | Attendee first name. |
| `middle_name` | Attendee middle name, if provided. |
| `last_name` | Attendee last name. |
| `suffix` | Name suffix, such as Jr. or III. |
| `affiliation` | School, university, agency, office, company, LGU, or organization. |
| `designation_category` | Attendee role/category, such as student, government official, speaker, employee, guest, or participant. |
| `sex` | `F` or `M`, matching the attendance sheet checkbox. |
| `email` | Email address. Used for duplicate checking within the same event. |
| `consent_documentation_publication` | Consent for photo/video/audio documentation and possible publication. |
| `consent_database_processing` | Consent for organizer database/future document processing. |
| `signature_text` | Optional typed/e-signature name. |
| `signature_image_path` | Optional captured/uploaded signature image path. |
| `submitted_at` | When the attendance was submitted. |
| `attendance_status` | `valid`, `duplicate`, `invalid`, or `void`. |
| `duplicate_flag` | Marks possible duplicate/spam records for review. |
| `created_at` | When the record was created. |
| `updated_at` | When the record was last updated. |

Important rule: official attendance sheet exports should include `valid` records only unless the office decides otherwise.

## `attendance_record_addresses`

Stores optional PSGC-coded address details for an attendance record.

| Column | Meaning |
| --- | --- |
| `address_id` | Unique address record ID. |
| `attendance_id` | Linked attendance record. References `attendance_records.attendance_id`. |
| `region_code` | Selected PSGC region. |
| `province_code` | Selected PSGC province. Nullable when not applicable. |
| `city_municipality_code` | Selected PSGC city/municipality. |
| `barangay_code` | Selected PSGC barangay. |
| `street_address` | House number, street, subdivision, purok, or similar detail. |
| `postal_code` | Optional postal code. |
| `created_at` | When the address row was created. |
| `updated_at` | When the address row was last updated. |

## `attendance_sheet_exports`

Stores generated/downloaded attendance sheet history.

| Column | Meaning |
| --- | --- |
| `export_id` | Unique export ID. |
| `event_id` | Event exported. References `events.event_id`. |
| `exported_by_user_id` | Admin who generated/downloaded the file. |
| `export_format` | `pdf`, `xlsx`, or `csv`. |
| `file_path` | Stored file path, if the system keeps a copy. |
| `total_records` | Number of attendance records included in that export. |
| `exported_at` | When the file was generated/downloaded. |

## `audit_logs`

Stores important actions for traceability.

| Column | Meaning |
| --- | --- |
| `audit_log_id` | Unique audit log ID. |
| `user_id` | Admin user who performed the action. Nullable for system/public events. |
| `action` | Action key, such as `created_event` or `generated_attendance_sheet`. |
| `entity_type` | Affected module/table, such as `event` or `attendance_record`. |
| `entity_id` | ID of the affected record. |
| `description` | Human-readable summary. |
| `old_values_json` | Previous values, if needed. |
| `new_values_json` | New values, if needed. |
| `ip_address` | IPv4/IPv6 address, if captured. |
| `user_agent` | Browser/client info, if captured. |
| `created_at` | When the action happened. |

## PSGC Lookup Tables

These tables store a local copy of official PSGC data from PSA. The attendance form should read from these tables instead of calling the PSA API live for every attendee.

### `psgc_regions`

| Column | Meaning |
| --- | --- |
| `region_code` | Official PSGC region code. |
| `region_name` | Region name. |
| `is_active` | Whether the row is selectable for new submissions. |
| `created_at` | When the row was imported/created. |
| `updated_at` | When the row was last updated. |

### `psgc_provinces`

| Column | Meaning |
| --- | --- |
| `province_code` | Official PSGC province code. |
| `region_code` | Parent PSGC region code. |
| `province_name` | Province name. |
| `is_active` | Whether the row is selectable for new submissions. |
| `created_at` | When the row was imported/created. |
| `updated_at` | When the row was last updated. |

### `psgc_cities_municipalities`

| Column | Meaning |
| --- | --- |
| `city_municipality_code` | Official PSGC city/municipality code. |
| `region_code` | Parent PSGC region code. |
| `province_code` | Parent PSGC province code, nullable where applicable. |
| `city_municipality_name` | City or municipality name. |
| `city_municipality_type` | `city` or `municipality`. |
| `is_active` | Whether the row is selectable for new submissions. |
| `created_at` | When the row was imported/created. |
| `updated_at` | When the row was last updated. |

### `psgc_barangays`

| Column | Meaning |
| --- | --- |
| `barangay_code` | Official PSGC barangay code. |
| `city_municipality_code` | Parent PSGC city/municipality code. |
| `barangay_name` | Barangay name. |
| `is_active` | Whether the row is selectable for new submissions. |
| `created_at` | When the row was imported/created. |
| `updated_at` | When the row was last updated. |
