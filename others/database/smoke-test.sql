-- Smoke test for the DICT attendance system schema.
-- Run after schema.sql and seed-core.sql.
--
-- This file intentionally inserts sample records into the database so the team can verify
-- table relationships, foreign keys, duplicate rules, export history, and audit logs.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

START TRANSACTION;

-- 1. Confirm expected table count.
SELECT 'table_count' AS check_name, COUNT(*) AS actual_count
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND table_type = 'BASE TABLE';

-- 2. Add sample DICT organizational units.
INSERT INTO organizational_units (
  parent_unit_id,
  unit_name,
  unit_type,
  unit_code,
  is_active
)
SELECT
  NULL,
  'DICT Region III',
  'regional_office',
  'DICT-R3',
  1
WHERE NOT EXISTS (
  SELECT 1 FROM organizational_units WHERE unit_code = 'DICT-R3'
);

INSERT INTO organizational_units (
  parent_unit_id,
  unit_name,
  unit_type,
  unit_code,
  is_active
)
SELECT
  parent.org_unit_id,
  'Technical Operations Division',
  'division',
  'DICT-R3-TOD',
  1
FROM organizational_units parent
WHERE parent.unit_code = 'DICT-R3'
  AND NOT EXISTS (
    SELECT 1 FROM organizational_units WHERE unit_code = 'DICT-R3-TOD'
  );

-- 3. Add sample admin users.
-- These password_hash values are placeholders for schema testing only.
INSERT INTO users (
  role_id,
  org_unit_id,
  full_name,
  email,
  password_hash,
  account_status
)
SELECT
  role_id,
  (SELECT org_unit_id FROM organizational_units WHERE unit_code = 'DICT-R3'),
  'Smoke Test Super Admin',
  'smoke.superadmin@example.test',
  '$2y$10$replace_with_real_hash_for_actual_login',
  'active'
FROM roles
WHERE role_name = 'super_admin'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  account_status = VALUES(account_status),
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO users (
  role_id,
  org_unit_id,
  full_name,
  email,
  password_hash,
  account_status
)
SELECT
  role_id,
  (SELECT org_unit_id FROM organizational_units WHERE unit_code = 'DICT-R3-TOD'),
  'Smoke Test Program Admin',
  'smoke.programadmin@example.test',
  '$2y$10$replace_with_real_hash_for_actual_login',
  'active'
FROM roles
WHERE role_name = 'program_admin'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  account_status = VALUES(account_status),
  updated_at = CURRENT_TIMESTAMP;

-- 4. Add a sample program and assign the Program Admin.
INSERT INTO programs (
  owning_unit_id,
  created_by_user_id,
  program_name,
  description,
  program_status
)
SELECT
  ou.org_unit_id,
  creator.user_id,
  'Free Wi-Fi for All',
  'Smoke test sample DICT program.',
  'active'
FROM organizational_units ou
CROSS JOIN users creator
WHERE ou.unit_code = 'DICT-R3-TOD'
  AND creator.email = 'smoke.superadmin@example.test'
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  program_status = VALUES(program_status),
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO program_admin_assignments (
  program_id,
  user_id,
  assigned_by_user_id,
  assignment_status,
  assigned_at,
  revoked_at
)
SELECT
  p.program_id,
  program_admin.user_id,
  super_admin.user_id,
  'active',
  CURRENT_TIMESTAMP,
  NULL
FROM programs p
CROSS JOIN users program_admin
CROSS JOIN users super_admin
WHERE p.program_name = 'Free Wi-Fi for All'
  AND program_admin.email = 'smoke.programadmin@example.test'
  AND super_admin.email = 'smoke.superadmin@example.test'
ON DUPLICATE KEY UPDATE
  assignment_status = 'active',
  revoked_at = NULL;

-- 5. Add a sample open event.
INSERT INTO events (
  program_id,
  created_by_user_id,
  event_title,
  event_description,
  venue,
  event_date,
  event_code,
  public_attendance_url,
  qr_code_path,
  event_status,
  opened_at,
  closed_at
)
SELECT
  p.program_id,
  program_admin.user_id,
  'Smoke Test Orientation',
  'Schema smoke test event.',
  'DICT Region III Office',
  CURRENT_DATE,
  'SMOKE-TEST-ORIENTATION',
  'https://example.test/attendance/SMOKE-TEST-ORIENTATION',
  'storage/qr/SMOKE-TEST-ORIENTATION.png',
  'open',
  CURRENT_TIMESTAMP,
  NULL
FROM programs p
CROSS JOIN users program_admin
WHERE p.program_name = 'Free Wi-Fi for All'
  AND program_admin.email = 'smoke.programadmin@example.test'
ON DUPLICATE KEY UPDATE
  event_title = VALUES(event_title),
  event_status = VALUES(event_status),
  opened_at = COALESCE(events.opened_at, VALUES(opened_at)),
  closed_at = NULL,
  updated_at = CURRENT_TIMESTAMP;

-- Snapshot ng fixed field defaults para sa sample event.
INSERT INTO event_attendance_field_settings (event_id, field_key, is_required)
SELECT e.event_id, f.field_key, f.default_is_required
FROM events e
CROSS JOIN attendance_form_fields f
WHERE e.event_code = 'SMOKE-TEST-ORIENTATION'
ON DUPLICATE KEY UPDATE
  is_required = event_attendance_field_settings.is_required;

-- 6. Insert minimal PSGC sample rows so address foreign keys can be tested.
INSERT INTO psgc_regions (region_code, region_name, is_active)
VALUES ('0300000000', 'Region III (Central Luzon)', 1)
ON DUPLICATE KEY UPDATE
  region_name = VALUES(region_name),
  is_active = 1,
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO psgc_provinces (province_code, region_code, province_name, is_active)
VALUES ('0314000000', '0300000000', 'Pampanga', 1)
ON DUPLICATE KEY UPDATE
  region_code = VALUES(region_code),
  province_name = VALUES(province_name),
  is_active = 1,
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO psgc_cities_municipalities (
  city_municipality_code,
  region_code,
  province_code,
  city_municipality_name,
  city_municipality_type,
  is_active
)
VALUES (
  '0314130000',
  '0300000000',
  '0314000000',
  'City of San Fernando',
  'city',
  1
)
ON DUPLICATE KEY UPDATE
  region_code = VALUES(region_code),
  province_code = VALUES(province_code),
  city_municipality_name = VALUES(city_municipality_name),
  city_municipality_type = VALUES(city_municipality_type),
  is_active = 1,
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO psgc_barangays (
  barangay_code,
  city_municipality_code,
  barangay_name,
  is_active
)
VALUES ('0314130001', '0314130000', 'San Agustin', 1)
ON DUPLICATE KEY UPDATE
  city_municipality_code = VALUES(city_municipality_code),
  barangay_name = VALUES(barangay_name),
  is_active = 1,
  updated_at = CURRENT_TIMESTAMP;

-- 7. Add a sample attendance record.
INSERT INTO attendance_records (
  event_id,
  first_name,
  middle_name,
  last_name,
  suffix,
  affiliation,
  designation_category,
  sex,
  email,
  consent_documentation_publication,
  consent_database_processing,
  signature_text,
  signature_image_path,
  submitted_at,
  attendance_status,
  duplicate_flag
)
SELECT
  e.event_id,
  'Maria',
  'Santos',
  'Reyes',
  NULL,
  'Municipality of San Fernando',
  'Government Official',
  'F',
  'maria.reyes@example.test',
  1,
  1,
  'Maria Santos Reyes',
  NULL,
  CURRENT_TIMESTAMP,
  'valid',
  0
FROM events e
WHERE e.event_code = 'SMOKE-TEST-ORIENTATION'
ON DUPLICATE KEY UPDATE
  affiliation = VALUES(affiliation),
  designation_category = VALUES(designation_category),
  attendance_status = 'valid',
  duplicate_flag = 0,
  updated_at = CURRENT_TIMESTAMP;

-- 8. Add one address row linked to the sample attendance record.
INSERT INTO attendance_record_addresses (
  attendance_id,
  region_code,
  province_code,
  city_municipality_code,
  barangay_code,
  street_address,
  postal_code
)
SELECT
  ar.attendance_id,
  '0300000000',
  '0314000000',
  '0314130000',
  '0314130001',
  'Sample Street',
  '2000'
FROM attendance_records ar
JOIN events e ON e.event_id = ar.event_id
WHERE e.event_code = 'SMOKE-TEST-ORIENTATION'
  AND ar.email = 'maria.reyes@example.test'
ON DUPLICATE KEY UPDATE
  street_address = VALUES(street_address),
  postal_code = VALUES(postal_code),
  updated_at = CURRENT_TIMESTAMP;

-- 9. Record an attendance sheet export and audit log.
INSERT INTO attendance_sheet_exports (
  event_id,
  exported_by_user_id,
  export_format,
  file_path,
  total_records,
  exported_at
)
SELECT
  e.event_id,
  program_admin.user_id,
  'pdf',
  'storage/exports/SMOKE-TEST-ORIENTATION.pdf',
  (
    SELECT COUNT(*)
    FROM attendance_records ar
    WHERE ar.event_id = e.event_id
      AND ar.attendance_status = 'valid'
  ),
  CURRENT_TIMESTAMP
FROM events e
CROSS JOIN users program_admin
WHERE e.event_code = 'SMOKE-TEST-ORIENTATION'
  AND program_admin.email = 'smoke.programadmin@example.test';

INSERT INTO audit_logs (
  user_id,
  action,
  entity_type,
  entity_id,
  description,
  old_values_json,
  new_values_json,
  ip_address,
  user_agent
)
SELECT
  program_admin.user_id,
  'smoke_test_generated_attendance_sheet',
  'event',
  e.event_id,
  'Smoke test generated a sample attendance sheet export.',
  NULL,
  JSON_OBJECT('event_code', e.event_code),
  '127.0.0.1',
  'mysql-cli-smoke-test'
FROM events e
CROSS JOIN users program_admin
WHERE e.event_code = 'SMOKE-TEST-ORIENTATION'
  AND program_admin.email = 'smoke.programadmin@example.test';

COMMIT;

-- 10. Verification queries.
SELECT 'roles' AS check_name, COUNT(*) AS total_rows FROM roles;
SELECT 'organizational_units' AS check_name, COUNT(*) AS total_rows FROM organizational_units;
SELECT 'users' AS check_name, COUNT(*) AS total_rows FROM users;
SELECT 'programs' AS check_name, COUNT(*) AS total_rows FROM programs;
SELECT 'program_admin_assignments' AS check_name, COUNT(*) AS total_rows FROM program_admin_assignments;
SELECT 'events' AS check_name, COUNT(*) AS total_rows FROM events;
SELECT 'attendance_form_fields' AS check_name, COUNT(*) AS total_rows FROM attendance_form_fields;
SELECT 'event_attendance_field_settings' AS check_name, COUNT(*) AS total_rows FROM event_attendance_field_settings;
SELECT 'attendance_records' AS check_name, COUNT(*) AS total_rows FROM attendance_records;
SELECT 'attendance_record_addresses' AS check_name, COUNT(*) AS total_rows FROM attendance_record_addresses;
SELECT 'attendance_sheet_exports' AS check_name, COUNT(*) AS total_rows FROM attendance_sheet_exports;
SELECT 'audit_logs' AS check_name, COUNT(*) AS total_rows FROM audit_logs;

SELECT
  'smoke_event_field_settings' AS check_name,
  COUNT(*) AS actual_count
FROM event_attendance_field_settings s
JOIN events e ON e.event_id = s.event_id
WHERE e.event_code = 'SMOKE-TEST-ORIENTATION';

SELECT
  e.event_code,
  e.event_title,
  p.program_name,
  admin.full_name AS created_by,
  COUNT(ar.attendance_id) AS valid_attendance_count
FROM events e
JOIN programs p ON p.program_id = e.program_id
JOIN users admin ON admin.user_id = e.created_by_user_id
LEFT JOIN attendance_records ar
  ON ar.event_id = e.event_id
  AND ar.attendance_status = 'valid'
WHERE e.event_code = 'SMOKE-TEST-ORIENTATION'
GROUP BY e.event_id, e.event_code, e.event_title, p.program_name, admin.full_name;

SELECT
  ar.attendance_id,
  CONCAT_WS(' ', ar.first_name, ar.middle_name, ar.last_name, ar.suffix) AS attendee_name,
  ar.affiliation,
  ar.designation_category,
  ar.email,
  ar.attendance_status,
  pr.region_name,
  pp.province_name,
  pcm.city_municipality_name,
  pb.barangay_name
FROM attendance_records ar
LEFT JOIN attendance_record_addresses ara ON ara.attendance_id = ar.attendance_id
LEFT JOIN psgc_regions pr ON pr.region_code = ara.region_code
LEFT JOIN psgc_provinces pp ON pp.province_code = ara.province_code
LEFT JOIN psgc_cities_municipalities pcm ON pcm.city_municipality_code = ara.city_municipality_code
LEFT JOIN psgc_barangays pb ON pb.barangay_code = ara.barangay_code
JOIN events e ON e.event_id = ar.event_id
WHERE e.event_code = 'SMOKE-TEST-ORIENTATION'
ORDER BY ar.attendance_id;

-- 11. Duplicate prevention check.
-- This should return duplicate_email_rows = 1 because schema enforces UNIQUE(event_id, email).
SELECT
  'duplicate_email_rows' AS check_name,
  COUNT(*) AS actual_count
FROM attendance_records ar
JOIN events e ON e.event_id = ar.event_id
WHERE e.event_code = 'SMOKE-TEST-ORIENTATION'
  AND ar.email = 'maria.reyes@example.test';
