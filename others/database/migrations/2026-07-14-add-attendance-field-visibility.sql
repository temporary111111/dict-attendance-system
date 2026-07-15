-- Adds show/hide control to the fixed per-event attendance fields.
-- Existing fields stay visible para walang mabagong old event form unexpectedly.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

ALTER TABLE event_attendance_field_settings
  ADD COLUMN is_visible TINYINT(1) NOT NULL DEFAULT 1 AFTER is_required,
  ADD CONSTRAINT chk_event_attendance_field_settings_visible
    CHECK (is_visible IN (0, 1));
