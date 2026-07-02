# MVP Requirements v1

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. System Purpose

The system will help DICT manage attendance records for programs and events involving external attendees. It will allow authorized administrators to create programs, create events under those programs, generate attendance QR codes or public links, collect attendance using a fixed system-provided attendance page, generate downloadable attendance sheets using the DICT template format, generate reports, and maintain an audit trail of important system activities.

The system is not intended to be an employee daily time-in/time-out system. It is focused on program/event-based attendance monitoring and reporting.

---

## 2. Updated MVP Approach

Important update:

* The system is no longer connected to Google Forms.
* The system will not include a form builder.
* The attendee attendance page will use fixed fields based on the required DICT attendance format.
* The PDF provided by the supervisor is treated as the downloadable attendance sheet/report template, not as a dynamic form builder requirement.
* After an event, an admin can generate and download an attendance sheet matching the DICT template.

The system will handle:

* Program management
* Event management
* Event attendance link and QR code generation
* Fixed public attendance submission
* Attendance validation
* Attendance records management
* Downloadable attendance sheet generation
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
* Generate attendance QR codes and links
* View all attendance records
* Generate and download attendance sheets
* View all reports
* Export reports
* View audit logs

### 3.2 Program Admin

The Program Admin can only access assigned programs and events under those programs.

The Program Admin can:

* View assigned programs
* Create and manage events under assigned programs
* Generate QR codes and public attendance links for events under assigned programs
* View attendance records for events under assigned programs
* Generate and download attendance sheets for events under assigned programs, if allowed by policy
* View reports for assigned programs and their events
* Export reports, if allowed by system policy

The Program Admin cannot:

* Manage users
* Access unassigned programs
* View attendance records from unassigned programs
* View reports from unassigned programs
* Modify system-wide settings

### 3.3 External Attendee

The External Attendee does not have a system account.

The External Attendee can:

* Open the event attendance page through a QR code or public link
* Submit attendance details through the fixed system attendance page

The External Attendee cannot:

* Log in to the admin system
* View reports
* Access admin features
* Edit other attendees' records

---

## 4. Core System Modules

## 4.1 Authentication Module

The system shall allow authorized administrators to log in securely.

Functional requirements:

* The system shall provide a login page for admin users.
* The system shall authenticate users using email/username and password.
* The system shall store passwords securely using password hashing.
* The system shall allow users to log out.
* The system shall restrict admin pages unless the user is logged in.
* The system shall support active/inactive user account status.

---

## 4.2 Role-Based Access Control Module

The system shall enforce user permissions based on role.

Functional requirements:

* The system shall support at least two admin roles: Super Admin and Program Admin.
* The system shall restrict Program Admins to assigned programs only.
* The system shall prevent Program Admins from accessing records outside their assigned programs.
* The system shall allow Super Admins to access all programs, events, records, reports, and audit logs.
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

Recommended MVP rule:

* Only Super Admin should create, edit, and archive programs.
* Program Admins should only view assigned programs and manage events under those programs.

---

## 4.5 Event Management Module

The system shall allow admins to create and manage events under programs.

Functional requirements:

* The system shall allow authorized users to create events under a program.
* The system shall allow authorized users to edit event details.
* The system shall allow authorized users to close or archive events based on role policy.
* The system shall store event title, description, venue, date, program, event code, public attendance URL, QR code path/data, and status.
* The system shall generate a public attendance link for each event.
* The system shall generate a QR code pointing to the event's public attendance page.
* The system shall allow each event to have a status such as draft, open, closed, or archived.

Event status rules:

* Draft: event is being prepared; attendance link is not yet active.
* Open: attendees can submit attendance.
* Closed: attendance collection is finished; reports and attendance sheet downloads are available.
* Archived: event is hidden from normal active views but kept for records.

---

## 4.6 Fixed Attendance Submission Module

The system shall provide a fixed public attendance page for each event.

Functional requirements:

* The system shall generate a unique public attendance URL for each event.
* The system shall generate a QR code for the public attendance URL.
* The public attendance page shall be accessible without a login.
* The public attendance page shall only accept submissions when the event status is open.
* The attendance form shall use fixed fields and shall not be dynamically built by admins.
* The attendance form shall include a privacy notice or consent text.
* The system shall validate submitted attendance data before saving.
* The system shall show a confirmation message after successful submission.

Recommended fixed attendance fields:

* First Name
* Middle Name
* Last Name
* Suffix
* School/University
* Designation/Category
* Sex
* Email Address
* Consent for photo/video/audio documentation and possible DICT publication
* Consent to be included in the organizer's database for future processing of relevant documents
* Signature field, if the office requires digital signature capture

Important note:

The supervisor-provided attendance sheet template has one `NAME` column, but the system should still store names in separated fields. The generated attendance sheet can combine first name, middle name, last name, and suffix into the displayed `NAME` column.

---

## 4.7 Attendance Validation Module

The system shall validate attendance submissions before storing them.

Functional requirements:

* The system shall validate required fields.
* The system shall validate email format.
* The system shall validate that only one sex option is selected.
* The system shall record consent responses.
* The system shall detect or flag duplicate submissions within the same event.
* The system shall prevent submissions for closed or archived events.

Duplicate checking for MVP:

* Same event + same email = duplicate or possible duplicate
* If email is missing by policy exception, same event + same normalized name + same school/university may be flagged for manual review

Name-only matching shall not be used as the primary duplicate check because it is unreliable.

---

## 4.8 Attendance Records Module

The system shall store attendance records per event.

Functional requirements:

* The system shall store attendance records linked to a specific event.
* The system shall store separated name fields: first name, middle name, last name, and suffix.
* The system shall store school/university, designation/category, sex, email, consent fields, submission timestamp, and attendance status.
* The system shall store optional signature data if digital signature capture is required.
* The system shall allow authorized users to view attendance records by event.
* The system shall allow authorized users to search and filter attendance records.
* The system shall avoid hard deletion of attendance records.

Recommended record statuses:

* valid
* duplicate
* invalid
* void

---

## 4.9 Attendance Sheet Generation Module

The system shall generate downloadable attendance sheets using the DICT template format provided by the supervisor.

Functional requirements:

* The system shall generate an attendance sheet for a selected event.
* The attendance sheet shall include the event title, venue, date, office heading, privacy notice, and attendance table.
* The attendance table shall follow the provided template columns:
  * row number
  * name
  * school/university
  * designation/category
  * sex: F/M
  * email address
  * consent for photo/video/audio documentation and possible publication
  * consent for organizer database/future processing
  * signature
* The system shall paginate rows as needed.
* The system shall allow authorized admins to download the generated attendance sheet.
* The system shall record attendance sheet download/export actions in the audit trail.

Recommended output formats:

* PDF for official printable attendance sheets
* Excel or CSV only if the office also needs editable tabular data

Important note:

The template is an output/report template. It is not a requirement to build a dynamic form builder.

---

## 4.10 Dashboard Module

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

## 4.11 Reports Module

The system shall generate reports per event and per program.

Functional requirements:

* The system shall generate an attendance report for a selected event.
* The system shall generate a summary report for a selected program.
* The system shall allow filtering by program, event, and date.
* The system shall allow exporting reports if allowed by policy.
* The system shall record report export actions in the audit trail.

Recommended report types:

### Event Attendance Sheet

This is the official downloadable attendance sheet based on the supervisor-provided template.

Includes:

* Program name
* Event title
* Event date
* Venue
* Privacy notice
* Total attendance records
* List of attendees in the required template format

### Program Summary Report

Includes:

* Program name
* Number of events
* Total attendance records
* Attendance count per event
* Date range covered

---

## 4.12 Audit Trail Module

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
* Opened event attendance
* Closed event attendance
* Archived event
* Generated QR code
* Submitted attendance, as a system event without exposing unnecessary personal data in the log
* Marked attendance as duplicate, invalid, or void
* Generated/downloaded attendance sheet
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
* attendance_sheet_exports
* audit_logs

Optional only if still required by the office:

* psgc_regions
* psgc_provinces
* psgc_cities_municipalities
* psgc_barangays

PSGC note:

The supervisor-provided attendance sheet template does not include address fields. PSGC should not be forced into the MVP attendance flow unless the supervisor confirms that address collection is still required outside the provided template.

---

## 6. Suggested Table Fields

### users

* id
* role_id
* full_name
* email
* password_hash
* status
* created_at
* updated_at

### roles

* id
* role_name
* description

### programs

* id
* program_name
* description
* office_or_division
* status
* created_by
* created_at
* updated_at

### program_admin_assignments

* id
* user_id
* program_id
* assigned_by
* assigned_at

### events

* id
* program_id
* event_title
* event_description
* venue
* event_date
* event_code
* public_attendance_url
* qr_code_path
* status
* created_by
* created_at
* updated_at

### attendance_records

* id
* event_id
* first_name
* middle_name
* last_name
* suffix
* school_university
* designation_category
* sex
* email
* consent_documentation_publication
* consent_database_processing
* signature_text optional
* signature_image_path optional
* submitted_at
* status
* duplicate_flag
* created_at
* updated_at

### attendance_sheet_exports

* id
* event_id
* exported_by
* export_format
* file_path optional
* total_records
* exported_at

### audit_logs

* id
* user_id nullable for public/system events
* action
* entity_type
* entity_id
* description
* old_value optional
* new_value optional
* ip_address optional
* user_agent optional
* created_at

---

## 7. Out of Scope for MVP

The following features should not be included in the MVP unless specifically required later:

* Google Forms integration
* Google Sheets automatic sync
* CSV attendance import as the main attendance flow
* Dynamic form builder
* Automatic generation of different custom forms per event
* Same-person detection across multiple events
* Attendee profile merging
* Biometrics
* Facial recognition
* RFID/NFC integration
* Mobile app
* SMS verification
* Email verification
* Advanced analytics

---

## 8. Phase 2 Enhancement Options

Possible future improvements:

* Digital signature capture if not included in MVP
* Editable report template settings, if the office later approves controlled customization
* PSGC-based address collection, if the office confirms that address is required
* Attendee profile management
* Same-person detection across events
* Unique attendee analytics
* Repeat attendee tracking
* Duplicate review and merge feature
* More advanced dashboard charts
* Scheduled report generation
* Optional CSV import for legacy attendance files

---

## 9. Key Assumptions

* External attendees will not have accounts.
* Admin users will be the only users who can log in.
* MySQL will be used as the database.
* Program Admins may be assigned to one or more programs.
* Attendance will be submitted through a fixed system page, not through Google Forms.
* The downloadable event attendance sheet will follow the supervisor-provided DICT template.
* The system will not provide a general-purpose form builder.
* Duplicate detection will only be handled within the same event during MVP.

---

## 10. Clarifications Needed from Supervisor

Before implementation, the following should be confirmed:

1. Should the public attendance form require digital signature capture, or should the signature column remain blank in the generated sheet?
2. Is email required for every attendee?
3. Should mobile number be collected even though it is not visible in the provided attendance sheet template?
4. Is PSGC/address collection still required, or is it removed because the provided template has no address columns?
5. Should Program Admins be assigned to one program only or multiple programs?
6. Who is allowed to download official attendance sheets?
7. What output formats are required: PDF, Excel, CSV, or all?
8. Should attendance submission be allowed only while event status is open?
9. Should admins be allowed to manually add/correct attendance records after the event closes?
10. What is the official data retention period and privacy wording to use?
11. Should Program Admins be allowed to view audit logs?
12. Should archived programs/events still be included in reports?

---

## 11. MVP Success Criteria

The MVP is considered successful if:

* Admin users can securely log in.
* Super Admin can manage programs and Program Admins.
* Program Admins can manage only assigned programs and events under those programs.
* Events can be created under programs.
* QR codes and public attendance links can be generated per event.
* External attendees can submit attendance through the fixed public attendance page.
* Attendance records are saved directly to MySQL.
* Duplicate or invalid submissions can be flagged.
* Attendance records can be viewed per event.
* Event attendance sheets can be generated and downloaded using the supervisor-provided DICT template.
* Reports can be generated per event and per program.
* Important admin actions are recorded in the audit trail.
* The system is usable for actual DICT program/event attendance monitoring.
