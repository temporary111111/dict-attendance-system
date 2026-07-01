# MVP Requirements v1

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. System Purpose

The system will help DICT manage attendance records for programs and events involving external attendees. It will allow authorized administrators to create programs, create events under those programs, generate QR codes or links connected to Google Forms, import attendance responses, generate reports, and maintain an audit trail of important system activities.

The system is not intended to be an employee daily time-in/time-out system. It is focused on program/event-based attendance monitoring and reporting.

---

## 2. Current MVP Approach

For the MVP, Google Forms will be used as the attendance collection tool. The system will not yet replace Google Forms with a custom attendance form.

The system will handle:

* Program management
* Event management
* Google Form link management
* QR code generation
* Attendance response import
* Attendance validation
* Dashboard summary
* Report generation
* Role-based access control
* Audit trail

---

## 3. User Roles

### 3.1 Super Admin

The Super Admin has full access to the system.

The Super Admin can:

* Manage admin accounts
* Manage all programs
* Assign Program Admins to programs
* Manage all events
* Generate QR codes
* Import attendance records
* View all reports
* Export reports
* View audit logs

### 3.2 Program Admin

The Program Admin can only access assigned programs and events under those programs.

The Program Admin can:

* View assigned programs
* Create and manage events under assigned programs
* Attach Google Form links to events
* Generate QR codes for assigned events
* Import attendance records for assigned events
* View reports for assigned programs/events
* Export reports, if allowed by system policy

The Program Admin cannot:

* Manage users
* Access unassigned programs
* View reports from unassigned programs
* Modify system-wide settings

### 3.3 External Attendee

The External Attendee does not have a system account.

The External Attendee can:

* Open the attendance form through a QR code or link
* Submit attendance details through Google Forms

The External Attendee cannot:

* Log in to the system
* View reports
* Access admin features

---

## 4. Core System Modules

## 4.1 Authentication Module

The system shall allow authorized administrators to log in securely.

Functional requirements:

* The system shall provide a login page for admin users.
* The system shall authenticate users using email/username and password.
* The system shall store passwords securely using password hashing.
* The system shall allow users to log out.
* The system shall restrict access to admin pages unless the user is logged in.
* The system shall support active/inactive user account status.

---

## 4.2 Role-Based Access Control Module

The system shall enforce user permissions based on role.

Functional requirements:

* The system shall support at least two admin roles: Super Admin and Program Admin.
* The system shall restrict Program Admins to assigned programs only.
* The system shall prevent Program Admins from accessing records outside their assigned programs.
* The system shall allow Super Admins to access all programs, events, records, and reports.
* The system shall record important role-related actions in the audit trail.

---

## 4.3 User Management Module

This module is for Super Admin use.

Functional requirements:

* The system shall allow the Super Admin to create admin accounts.
* The system shall allow the Super Admin to edit admin account details.
* The system shall allow the Super Admin to activate or deactivate admin accounts.
* The system shall allow the Super Admin to assign a Program Admin to one or more programs.
* The system shall prevent external attendees from being created as login users.

---

## 4.4 Program Management Module

The system shall allow admins to manage DICT programs.

Functional requirements:

* The system shall allow authorized users to create programs.
* The system shall allow authorized users to edit program details.
* The system shall allow authorized users to archive programs.
* The system shall store program name, description, office/division, status, creator, and timestamps.
* The system shall allow viewing of events under each program.
* The system shall allow Super Admins to assign Program Admins to programs.

---

## 4.5 Event Management Module

The system shall allow admins to create and manage events under programs.

Functional requirements:

* The system shall allow authorized users to create events under a program.
* The system shall allow authorized users to edit event details.
* The system shall allow authorized users to archive events.
* The system shall store event title, description, venue, date, program, event code, Google Form link, and status.
* The system shall allow each event to have its own Google Form link.
* The system shall allow each event to have a status such as draft, open, closed, or archived.
* The system shall allow authorized users to generate a QR code for the event attendance link.
* The QR code shall point to the assigned Google Form link or pre-filled Google Form link.

---

## 4.6 Attendance Collection Using Google Forms

For the MVP, attendance data will be collected through Google Forms.

Functional requirements:

* The system shall store the Google Form link assigned to each event.
* The system shall generate a QR code based on the assigned Google Form link.
* The Google Form should collect attendee details using a standard format.
* The Google Form should include an event code field when possible.
* The Google Form should include a data privacy notice or consent checkbox.

Recommended Google Form fields:

* Event Code
* First Name
* Middle Name
* Last Name
* Suffix
* Email Address
* Mobile Number
* Region
* Province
* City/Municipality
* Barangay
* Street/Purok/Sitio
* Agency/Organization, if needed
* Data Privacy Consent

---

## 4.7 Attendance Import Module

The system shall allow attendance responses from Google Forms to be imported into MySQL.

For the MVP, the recommended method is CSV import from Google Forms or Google Sheets.

Functional requirements:

* The system shall allow authorized users to import attendance responses for a selected event.
* The system shall validate required fields during import.
* The system shall detect missing or invalid required values.
* The system shall store successful attendance records in the database.
* The system shall reject or flag invalid rows.
* The system shall record the import batch details.
* The system shall show the number of successful, failed, and duplicate records.
* The system shall prevent or flag duplicate submissions within the same event.

Duplicate checking for MVP:

* Same event + same email = duplicate or possible duplicate
* Same event + same mobile number = duplicate or possible duplicate

Name-only matching shall not be used as the primary duplicate check because it is unreliable.

---

## 4.8 Attendance Records Module

The system shall store imported attendance records per event.

Functional requirements:

* The system shall store attendance records linked to a specific event.
* The system shall store separated name fields: first name, middle name, last name, and suffix.
* The system shall store contact information such as email and/or mobile number.
* The system shall store address-related data using PSGC-aware fields.
* The system shall store the response timestamp from Google Forms when available.
* The system shall store the import source and import batch.
* The system shall allow authorized users to view attendance records by event.
* The system shall allow authorized users to search and filter attendance records.

---

## 4.9 Dashboard Module

The system shall provide summary information to admins.

Functional requirements:

* The system shall display total number of programs.
* The system shall display total number of events.
* The system shall display total number of attendance records.
* The system shall display recent events.
* The system shall display attendance count per event.
* The system shall display attendance count per program.
* Program Admins shall only see dashboard data for assigned programs.

---

## 4.10 Reports Module

The system shall generate reports per event and per program.

Functional requirements:

* The system shall generate an attendance report for a selected event.
* The system shall generate a summary report for a selected program.
* The system shall allow filtering by program, event, and date.
* The system shall allow exporting reports.
* The system shall record report export actions in the audit trail.

Recommended report types:

### Event Attendance Report

Includes:

* Program name
* Event title
* Event date
* Venue
* Total attendance records
* List of attendees
* Timestamp of submission
* Address fields
* Contact fields, if allowed

### Program Summary Report

Includes:

* Program name
* Number of events
* Total attendance records
* Attendance count per event
* Date range covered

---

## 4.11 Audit Trail Module

The system shall record important admin actions.

Functional requirements:

* The system shall log important actions performed by admins.
* The audit trail shall include the user, action, affected entity, description, and timestamp.
* The system shall allow Super Admins to view audit logs.
* Program Admin audit log visibility may be limited or disabled depending on office policy.

Actions to log:

* Admin login
* Admin logout
* Created program
* Updated program
* Archived program
* Assigned Program Admin
* Created event
* Updated event
* Archived event
* Added or updated Google Form link
* Generated QR code
* Imported attendance records
* Exported report
* Activated/deactivated user account

---

## 5. Recommended MVP Database Tables

The MVP database should include:

* users
* roles
* programs
* program_admin_assignments
* events
* attendance_records
* attendance_import_batches
* audit_logs
* psgc_regions
* psgc_provinces
* psgc_cities_municipalities
* psgc_barangays

---

## 6. Out of Scope for MVP

The following features should not be included in the MVP unless specifically required later:

* Custom built-in attendance form
* Automatic Google Forms creation
* Full Google Forms API integration
* Automatic Google Sheets sync
* Same-person detection across multiple events
* Attendee profile merging
* Biometrics
* Facial recognition
* RFID/NFC integration
* Mobile app
* SMS verification
* Email verification
* Advanced analytics

These can be considered for Phase 2 or future versions.

---

## 7. Phase 2 Enhancement Options

Possible future improvements:

* Google Sheets automatic sync
* Google Forms API or Apps Script integration
* Built-in custom attendance form
* PSGC cascading dropdowns
* Attendee profile management
* Same-person detection across events
* Unique attendee analytics
* Repeat attendee tracking
* Duplicate review and merge feature
* More advanced dashboard charts
* Scheduled report generation

---

## 8. Key Assumptions

* Google Forms will be used as the attendance collection tool for the MVP.
* External attendees will not have accounts.
* Admin users will be the only users who can log in.
* MySQL will be used as the database.
* Program Admins may be assigned to one or more programs.
* CSV import will be the initial method for importing Google Forms responses.
* Duplicate detection will only be handled within the same event during MVP.
* PSGC-related address handling is required.

---

## 9. Clarifications Needed from Supervisor

Before implementation, the following should be confirmed:

1. Will Google Forms be permanent, or only used for Phase 1?
2. Who will create the Google Forms manually?
3. Should the system only store Google Form links, or should it later generate/manage forms?
4. Should responses be imported manually via CSV, or synced automatically from Google Sheets?
5. What exact fields are required in the Google Form?
6. Is email required, mobile required, or at least one of the two?
7. Are Program Admins assigned to one program only or multiple programs?
8. Who is allowed to export reports?
9. What report formats are required: CSV, Excel, PDF, or all?
10. What is the expected data retention period?
11. Should Program Admins be allowed to view audit logs?
12. Should archived programs/events still be included in reports?

---

## 10. MVP Success Criteria

The MVP is considered successful if:

* Admin users can securely log in.
* Super Admin can manage programs and Program Admins.
* Program Admins can manage only assigned programs/events.
* Events can be created under programs.
* Google Form links can be attached to events.
* QR codes can be generated for event attendance.
* Google Form responses can be imported into the system.
* Attendance records can be viewed per event.
* Reports can be generated per event and per program.
* Important admin actions are recorded in the audit trail.
* The system is usable for actual DICT program/event attendance monitoring.
