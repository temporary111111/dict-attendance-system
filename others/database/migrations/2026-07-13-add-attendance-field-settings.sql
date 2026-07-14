-- One-time migration for configurable fixed attendance-field requirements.
-- Safe itong i-run ulit: table creation, seeds, at backfill are idempotent.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE IF NOT EXISTS attendance_form_fields (
  field_key VARCHAR(100) NOT NULL,
  field_label VARCHAR(150) NOT NULL,
  default_is_required TINYINT(1) NOT NULL,
  is_admin_configurable TINYINT(1) NOT NULL,
  display_order SMALLINT UNSIGNED NOT NULL,
  PRIMARY KEY (field_key),
  UNIQUE KEY uq_attendance_form_fields_display_order (display_order),
  CONSTRAINT chk_attendance_form_fields_default_required
    CHECK (default_is_required IN (0, 1)),
  CONSTRAINT chk_attendance_form_fields_admin_configurable
    CHECK (is_admin_configurable IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS event_attendance_field_settings (
  event_id BIGINT UNSIGNED NOT NULL,
  field_key VARCHAR(100) NOT NULL,
  is_required TINYINT(1) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (event_id, field_key),
  KEY idx_event_attendance_field_settings_field_key (field_key),
  CONSTRAINT fk_event_attendance_field_settings_event
    FOREIGN KEY (event_id) REFERENCES events (event_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_event_attendance_field_settings_field
    FOREIGN KEY (field_key) REFERENCES attendance_form_fields (field_key)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_event_attendance_field_settings_required
    CHECK (is_required IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

INSERT INTO event_attendance_field_settings (event_id, field_key, is_required)
SELECT e.event_id, f.field_key, f.default_is_required
FROM events e
CROSS JOIN attendance_form_fields f
ON DUPLICATE KEY UPDATE
  is_required = event_attendance_field_settings.is_required;

ALTER TABLE attendance_records
  MODIFY COLUMN affiliation VARCHAR(200) NULL,
  MODIFY COLUMN designation_category VARCHAR(150) NULL,
  MODIFY COLUMN sex ENUM('F', 'M') NULL;
