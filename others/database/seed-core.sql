-- Core seed data for the DICT attendance system.
-- Run after schema.sql.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

INSERT INTO roles (role_name, description, is_active)
VALUES
  ('super_admin', 'Full system administrator with access to all programs, events, reports, and audit logs.', 1),
  ('program_admin', 'DICT employee assigned to manage events and attendance for assigned programs.', 1)
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  is_active = VALUES(is_active),
  updated_at = CURRENT_TIMESTAMP;

INSERT INTO organizational_units (
  parent_unit_id,
  unit_name,
  unit_type,
  unit_code,
  is_active
)
VALUES (
  NULL,
  'Department of Information and Communications Technology',
  'department',
  'DICT',
  1
)
ON DUPLICATE KEY UPDATE
  unit_name = VALUES(unit_name),
  unit_type = VALUES(unit_type),
  is_active = VALUES(is_active),
  updated_at = CURRENT_TIMESTAMP;

-- Fixed system fields lang ito. Walang admin CRUD para hindi maging form builder.
INSERT INTO attendance_form_fields (
  field_key,
  field_label,
  default_is_required,
  is_admin_configurable,
  display_order
)
VALUES
  ('first_name', 'First name', 1, 0, 1),
  ('middle_name', 'Middle name', 0, 1, 2),
  ('last_name', 'Last name', 1, 0, 3),
  ('suffix', 'Suffix', 0, 1, 4),
  ('affiliation', 'Affiliation', 1, 1, 5),
  ('designation_category', 'Designation/category', 1, 1, 6),
  ('sex', 'Sex', 1, 1, 7),
  ('email', 'Email', 1, 0, 8),
  ('consent_documentation_publication', 'Documentation/publication consent', 1, 1, 9),
  ('consent_database_processing', 'Database-processing consent', 1, 0, 10),
  ('signature', 'Signature', 0, 1, 11),
  ('psgc_address', 'PSGC address', 0, 1, 12),
  ('street_address', 'Street address', 0, 1, 13),
  ('postal_code', 'Postal code', 0, 1, 14)
ON DUPLICATE KEY UPDATE
  field_label = VALUES(field_label),
  default_is_required = VALUES(default_is_required),
  is_admin_configurable = VALUES(is_admin_configurable),
  display_order = VALUES(display_order);

-- Optional setup notes:
--
-- 1. Create the first Super Admin account through the application or a secure admin setup command.
--    Do not store or write plain-text passwords in SQL files.
--
-- 2. If you need a temporary local development admin, generate a password hash using the same
--    password-hashing library used by the application, then insert it manually.
--
-- Example shape only:
--
-- INSERT INTO users (
--   role_id,
--   org_unit_id,
--   full_name,
--   email,
--   password_hash,
--   account_status
-- )
-- SELECT
--   r.role_id,
--   ou.org_unit_id,
--   'System Super Admin',
--   'admin@example.com',
--   '<replace-with-real-password-hash>',
--   'active'
-- FROM roles r
-- JOIN organizational_units ou ON ou.unit_code = 'DICT'
-- WHERE r.role_name = 'super_admin';
--
-- 3. Program examples are intentionally not seeded by default because ownership depends on
--    the actual DICT office/division/unit confirmed by the team.
--
-- Example program names:
-- - Free Wi-Fi for All
-- - eGov Super App
-- - National Broadband Plan
