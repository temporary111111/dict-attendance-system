-- MySQL schema for the DICT Program and Event Attendance Monitoring and Reporting System.
-- Based on others/erd/normalized-mysql-erd.md.
-- Target: MySQL 8.0+ / InnoDB / utf8mb4.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE IF NOT EXISTS roles (
  role_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  role_name VARCHAR(50) NOT NULL,
  description VARCHAR(255) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (role_id),
  UNIQUE KEY uq_roles_role_name (role_name),
  CONSTRAINT chk_roles_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS organizational_units (
  org_unit_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  parent_unit_id BIGINT UNSIGNED NULL,
  unit_name VARCHAR(200) NOT NULL,
  unit_type VARCHAR(50) NOT NULL,
  unit_code VARCHAR(50) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (org_unit_id),
  UNIQUE KEY uq_organizational_units_unit_code (unit_code),
  KEY idx_organizational_units_parent_unit_id (parent_unit_id),
  KEY idx_organizational_units_unit_type (unit_type),
  CONSTRAINT fk_organizational_units_parent
    FOREIGN KEY (parent_unit_id) REFERENCES organizational_units (org_unit_id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT chk_organizational_units_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  role_id BIGINT UNSIGNED NOT NULL,
  org_unit_id BIGINT UNSIGNED NULL,
  full_name VARCHAR(150) NOT NULL,
  email VARCHAR(150) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  account_status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_users_email (email),
  KEY idx_users_role_id (role_id),
  KEY idx_users_org_unit_id (org_unit_id),
  KEY idx_users_account_status (account_status),
  CONSTRAINT fk_users_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_users_org_unit
    FOREIGN KEY (org_unit_id) REFERENCES organizational_units (org_unit_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS programs (
  program_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  owning_unit_id BIGINT UNSIGNED NOT NULL,
  created_by_user_id BIGINT UNSIGNED NOT NULL,
  program_name VARCHAR(200) NOT NULL,
  description TEXT NULL,
  logo_path VARCHAR(500) DEFAULT NULL,
  program_status ENUM('active', 'archived') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (program_id),
  UNIQUE KEY uq_programs_owning_unit_name (owning_unit_id, program_name),
  KEY idx_programs_owning_unit_id (owning_unit_id),
  KEY idx_programs_created_by_user_id (created_by_user_id),
  KEY idx_programs_program_status (program_status),
  CONSTRAINT fk_programs_owning_unit
    FOREIGN KEY (owning_unit_id) REFERENCES organizational_units (org_unit_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_programs_created_by_user
    FOREIGN KEY (created_by_user_id) REFERENCES users (user_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS program_admin_assignments (
  assignment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  program_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  assigned_by_user_id BIGINT UNSIGNED NOT NULL,
  assignment_status ENUM('active', 'revoked') NOT NULL DEFAULT 'active',
  assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  revoked_at DATETIME NULL,
  PRIMARY KEY (assignment_id),
  UNIQUE KEY uq_program_admin_assignments_program_user (program_id, user_id),
  KEY idx_program_admin_assignments_user_id (user_id),
  KEY idx_program_admin_assignments_assigned_by_user_id (assigned_by_user_id),
  KEY idx_program_admin_assignments_assignment_status (assignment_status),
  CONSTRAINT fk_program_admin_assignments_program
    FOREIGN KEY (program_id) REFERENCES programs (program_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_program_admin_assignments_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_program_admin_assignments_assigned_by_user
    FOREIGN KEY (assigned_by_user_id) REFERENCES users (user_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_program_admin_assignments_revoked_at
    CHECK (
      (assignment_status = 'active' AND revoked_at IS NULL)
      OR (assignment_status = 'revoked' AND revoked_at IS NOT NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

CREATE TABLE IF NOT EXISTS events (
  event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  program_id BIGINT UNSIGNED NOT NULL,
  created_by_user_id BIGINT UNSIGNED NOT NULL,
  event_title VARCHAR(200) NOT NULL,
  event_description TEXT NULL,
  venue VARCHAR(255) NOT NULL,
  event_date DATE NOT NULL,
  event_code VARCHAR(100) NOT NULL,
  public_attendance_url VARCHAR(500) NULL,
  qr_code_path VARCHAR(500) NULL,
  event_status ENUM('draft', 'open', 'closed', 'archived') NOT NULL DEFAULT 'draft',
  opened_at DATETIME NULL,
  closed_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (event_id),
  UNIQUE KEY uq_events_event_code (event_code),
  KEY idx_events_program_id (program_id),
  KEY idx_events_created_by_user_id (created_by_user_id),
  KEY idx_events_event_date (event_date),
  KEY idx_events_event_status (event_status),
  CONSTRAINT fk_events_program
    FOREIGN KEY (program_id) REFERENCES programs (program_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_events_created_by_user
    FOREIGN KEY (created_by_user_id) REFERENCES users (user_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_events_status_dates
    CHECK (
      (event_status <> 'open' OR opened_at IS NOT NULL)
      AND (event_status <> 'closed' OR closed_at IS NOT NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS event_attendance_field_settings (
  event_id BIGINT UNSIGNED NOT NULL,
  field_key VARCHAR(100) NOT NULL,
  is_required TINYINT(1) NOT NULL,
  is_visible TINYINT(1) NOT NULL DEFAULT 1,
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
    CHECK (is_required IN (0, 1)),
  CONSTRAINT chk_event_attendance_field_settings_visible
    CHECK (is_visible IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS attendance_records (
  attendance_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  event_id BIGINT UNSIGNED NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  middle_name VARCHAR(100) NULL,
  last_name VARCHAR(100) NOT NULL,
  suffix VARCHAR(30) NULL,
  affiliation VARCHAR(200) NULL,
  designation_category VARCHAR(150) NULL,
  sex ENUM('F', 'M') NULL,
  email VARCHAR(150) NOT NULL,
  consent_documentation_publication TINYINT(1) NOT NULL DEFAULT 0,
  consent_database_processing TINYINT(1) NOT NULL DEFAULT 0,
  signature_text VARCHAR(150) NULL,
  signature_image_path VARCHAR(500) NULL,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  attendance_status ENUM('valid', 'duplicate', 'invalid', 'void') NOT NULL DEFAULT 'valid',
  duplicate_flag TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (attendance_id),
  UNIQUE KEY uq_attendance_records_event_email (event_id, email),
  KEY idx_attendance_records_event_id (event_id),
  KEY idx_attendance_records_email (email),
  KEY idx_attendance_records_status (attendance_status),
  KEY idx_attendance_records_duplicate_flag (duplicate_flag),
  KEY idx_attendance_records_submitted_at (submitted_at),
  CONSTRAINT fk_attendance_records_event
    FOREIGN KEY (event_id) REFERENCES events (event_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_attendance_records_consent_documentation
    CHECK (consent_documentation_publication IN (0, 1)),
  CONSTRAINT chk_attendance_records_consent_database
    CHECK (consent_database_processing IN (0, 1)),
  CONSTRAINT chk_attendance_records_duplicate_flag
    CHECK (duplicate_flag IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS attendance_sheet_exports (
  export_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  event_id BIGINT UNSIGNED NOT NULL,
  exported_by_user_id BIGINT UNSIGNED NOT NULL,
  export_format ENUM('pdf', 'xlsx', 'csv') NOT NULL DEFAULT 'pdf',
  file_path VARCHAR(500) NULL,
  total_records INT UNSIGNED NOT NULL DEFAULT 0,
  exported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (export_id),
  KEY idx_attendance_sheet_exports_event_id (event_id),
  KEY idx_attendance_sheet_exports_exported_by_user_id (exported_by_user_id),
  KEY idx_attendance_sheet_exports_exported_at (exported_at),
  CONSTRAINT fk_attendance_sheet_exports_event
    FOREIGN KEY (event_id) REFERENCES events (event_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_attendance_sheet_exports_exported_by_user
    FOREIGN KEY (exported_by_user_id) REFERENCES users (user_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS audit_logs (
  audit_log_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NULL,
  action VARCHAR(100) NOT NULL,
  entity_type VARCHAR(100) NOT NULL,
  entity_id BIGINT UNSIGNED NULL,
  description VARCHAR(500) NOT NULL,
  old_values_json JSON NULL,
  new_values_json JSON NULL,
  ip_address VARCHAR(45) NULL,
  user_agent VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (audit_log_id),
  KEY idx_audit_logs_user_id (user_id),
  KEY idx_audit_logs_action (action),
  KEY idx_audit_logs_entity (entity_type, entity_id),
  KEY idx_audit_logs_created_at (created_at),
  CONSTRAINT fk_audit_logs_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS psgc_regions (
  region_code VARCHAR(10) NOT NULL,
  region_name VARCHAR(150) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (region_code),
  KEY idx_psgc_regions_is_active (is_active),
  CONSTRAINT chk_psgc_regions_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS psgc_provinces (
  province_code VARCHAR(10) NOT NULL,
  region_code VARCHAR(10) NOT NULL,
  province_name VARCHAR(150) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (province_code),
  KEY idx_psgc_provinces_region_code (region_code),
  KEY idx_psgc_provinces_is_active (is_active),
  CONSTRAINT fk_psgc_provinces_region
    FOREIGN KEY (region_code) REFERENCES psgc_regions (region_code)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_psgc_provinces_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS psgc_cities_municipalities (
  city_municipality_code VARCHAR(10) NOT NULL,
  region_code VARCHAR(10) NOT NULL,
  province_code VARCHAR(10) NULL,
  city_municipality_name VARCHAR(150) NOT NULL,
  city_municipality_type ENUM('city', 'municipality') NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (city_municipality_code),
  KEY idx_psgc_cities_municipalities_region_code (region_code),
  KEY idx_psgc_cities_municipalities_province_code (province_code),
  KEY idx_psgc_cities_municipalities_is_active (is_active),
  CONSTRAINT fk_psgc_cities_municipalities_region
    FOREIGN KEY (region_code) REFERENCES psgc_regions (region_code)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_psgc_cities_municipalities_province
    FOREIGN KEY (province_code) REFERENCES psgc_provinces (province_code)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_psgc_cities_municipalities_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS psgc_barangays (
  barangay_code VARCHAR(10) NOT NULL,
  city_municipality_code VARCHAR(10) NOT NULL,
  barangay_name VARCHAR(150) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (barangay_code),
  KEY idx_psgc_barangays_city_municipality_code (city_municipality_code),
  KEY idx_psgc_barangays_is_active (is_active),
  CONSTRAINT fk_psgc_barangays_city_municipality
    FOREIGN KEY (city_municipality_code) REFERENCES psgc_cities_municipalities (city_municipality_code)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_psgc_barangays_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS attendance_record_addresses (
  address_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  attendance_id BIGINT UNSIGNED NOT NULL,
  region_code VARCHAR(10) NOT NULL,
  province_code VARCHAR(10) NULL,
  city_municipality_code VARCHAR(10) NOT NULL,
  barangay_code VARCHAR(10) NOT NULL,
  street_address VARCHAR(255) NULL,
  postal_code VARCHAR(10) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (address_id),
  UNIQUE KEY uq_attendance_record_addresses_attendance_id (attendance_id),
  KEY idx_attendance_record_addresses_region_code (region_code),
  KEY idx_attendance_record_addresses_province_code (province_code),
  KEY idx_attendance_record_addresses_city_municipality_code (city_municipality_code),
  KEY idx_attendance_record_addresses_barangay_code (barangay_code),
  CONSTRAINT fk_attendance_record_addresses_attendance
    FOREIGN KEY (attendance_id) REFERENCES attendance_records (attendance_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_attendance_record_addresses_region
    FOREIGN KEY (region_code) REFERENCES psgc_regions (region_code)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_attendance_record_addresses_province
    FOREIGN KEY (province_code) REFERENCES psgc_provinces (province_code)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_attendance_record_addresses_city_municipality
    FOREIGN KEY (city_municipality_code) REFERENCES psgc_cities_municipalities (city_municipality_code)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_attendance_record_addresses_barangay
    FOREIGN KEY (barangay_code) REFERENCES psgc_barangays (barangay_code)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
