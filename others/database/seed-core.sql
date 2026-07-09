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
