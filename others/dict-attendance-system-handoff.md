# DICT Program & Event Attendance Monitoring System

## Final Handoff Document

---

## 1. System Overview

### 1.1 System Type

Internal DICT web system for:

* Program management
* Event management
* Fixed public attendance submission
* Attendance records management
* Template-based attendance sheet generation
* Reporting and audit logging

NOT:

* Time-in/time-out system
* Thesis-only prototype
* Mobile app system
* Biometric/RFID system
* Dynamic form builder
* Google Forms integration system

---

## 1.2 Core Purpose

Manage DICT program/event attendance by letting external attendees submit attendance through a fixed public event page, then generating official downloadable attendance sheets based on the DICT template provided by the supervisor.

---

## 2. Critical Architecture Decision

## Fixed Attendance Page Rule

* The system collects attendance directly.
* External attendees do not create accounts.
* Each event has a public attendance link and QR code.
* The public attendance page uses fixed fields.
* Admins do not create custom forms.

## Template Output Rule

* The supervisor-provided PDF is the attendance sheet/report template.
* The template is generated/downloaded by the admin after or during the event.
* The template is not a form builder requirement.

---

## 3. Attendance Flow

1. Admin creates Program.
2. Admin creates Event.
3. Admin opens event attendance.
4. System generates public attendance link and QR code.
5. External attendee opens the link or scans the QR code.
6. External attendee submits fixed attendance fields.
7. System validates and stores the record in MySQL.
8. Admin closes the event after attendance collection.
9. Admin generates/downloads the DICT attendance sheet.
10. System generates reports and audit logs.

---

## 4. System Roles

## Super Admin

* Full system access
* Manage users, programs, events
* Assign Program Admins
* View all attendance records
* Generate/download all attendance sheets
* View reports and audit logs

## Program Admin

* Access assigned programs only
* Manage events under assigned programs
* Generate event attendance links and QR codes
* View assigned event attendance records
* Generate/download assigned attendance sheets, if allowed
* Generate reports with limited scope

## External Attendee

* No login
* Opens public attendance link or QR code
* Submits fixed attendance details only

---

## 5. Core Modules

* Authentication
* Role-Based Access Control
* User Management
* Program Management
* Event Management
* Attendance Link and QR Code Generation
* Fixed Attendance Submission
* Attendance Validation
* Attendance Records
* Attendance Sheet Generation
* Reporting
* Audit Trail

---

## 6. Attendance Rules

## Source Rule

Attendance source is:

Public event link / QR code -> Fixed system attendance page -> MySQL

No Google Forms or CSV import in the core MVP flow.

## Duplicate Rule

Only within same event:

* Event ID + Email

## Identifier Rule

* Email is the primary duplicate identifier.
* Name-only matching is not reliable.
* Cross-event identity matching is not part of MVP.

---

## 7. Event Rules

Hierarchy:

Program -> Event -> Attendance Records -> Attendance Sheet

Statuses:

* Draft
* Open
* Closed
* Archived

Rules:

* Draft events do not accept attendance.
* Open events accept public attendance submissions.
* Closed events stop attendance collection but allow reports/downloads.
* Archived events are hidden from active views but retained.

---

## 8. Attendance Sheet Template Rules

The generated attendance sheet should follow the supervisor-provided DICT template.

Template fields:

* Title of event/seminar/meeting
* Venue
* Date
* Privacy notice
* Name
* School/University
* Designation/Category
* Sex: F/M
* Email address
* Consent for photo/video/audio documentation and possible publication
* Consent for organizer database/future processing
* Signature

Implementation note:

Store names in separated fields in the database, then combine them into the `NAME` column during report generation.

---

## 9. Data Integrity Rules

* No hard delete for attendance records.
* Use status-based records:
  * valid
  * duplicate
  * invalid
  * void
* Attendance sheet downloads must be logged.
* Report exports must be logged.
* Audit logs should be read-only and should not be deleted from the application.

---

## 10. Privacy Rules

* Collect only fields needed for the attendance workflow and official attendance sheet.
* Do not collect government ID unless explicitly required.
* Consent responses must be stored.
* The privacy notice in the generated sheet should match the office-approved wording.
* Clarify whether digital signature is required.

---

## 11. Database Tables

Recommended MVP tables:

* users
* roles
* programs
* program_admin_assignments
* events
* attendance_records
* attendance_sheet_exports
* audit_logs

Optional only if required later:

* psgc_regions
* psgc_provinces
* psgc_cities_municipalities
* psgc_barangays

---

## 12. Critical Warnings

* Do not build a form builder for MVP.
* Do not keep old Google Forms/CSV import assumptions in the core workflow.
* Do not implement cross-event identity matching in MVP.
* Do not rely on name-only duplicate detection.
* Do not allow weak RBAC.
* Do not hard delete attendance records.
* Clarify signature handling before implementation.
* Clarify whether PSGC/address collection is still required, because the provided template has no address columns.

---

## 13. DFD Status

Text DFD documents should follow the updated system direction:

* Level 0: System context without Google Forms
* Level 1: Main internal processes including fixed attendance submission and attendance sheet generation
* Level 2: Detailed attendance submission, validation, storage, and sheet generation

Existing visual PNG diagrams may need regeneration if they still show Google Forms or CSV import.

---

## End of Document
