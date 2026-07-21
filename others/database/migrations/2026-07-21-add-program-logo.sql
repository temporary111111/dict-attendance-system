-- Adds program logo storage support.
-- Super Admin can upload program logos which will show up on forms and PDFs.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

ALTER TABLE programs
  ADD COLUMN logo_path VARCHAR(500) DEFAULT NULL AFTER description;
