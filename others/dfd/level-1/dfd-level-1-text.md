# DFD Level 1

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This DFD Level 1 shows the major internal processes of the system and how data flows between external entities, system processes, and data stores.

Unlike DFD Level 0, which shows the system as one whole process, DFD Level 1 breaks the system into core functions.

Important update:

The MVP no longer uses Google Forms, Google Sheets, or CSV import as the primary attendance flow. Attendance is submitted through the system's fixed public attendance page.

---

## 2. External Entities

The external entities are:

1. Super Admin
2. Program Admin
3. External Attendee

The DICT Attendance Sheet Template is not an external entity in the MVP. It is a fixed output format used by the attendance sheet generation process.

---

## 3. Data Stores

### D1 Users

Stores admin user accounts.

Includes:

* User ID
* Name
* Email/username
* Password hash
* Role ID
* Account status

---

### D2 Roles and Program Assignments

Stores user roles and program assignments.

Includes:

* Role records
* User-to-program assignments
* Permission-related records

---

### D3 Programs

Stores DICT program records.

Includes:

* Program ID
* Program name
* Description
* Office/division
* Status
* Created by
* Timestamps

---

### D4 Events

Stores event records under programs.

Includes:

* Event ID
* Program ID
* Event title
* Description
* Venue
* Event date
* Event code
* Public attendance URL
* QR code path/data
* Status
* Timestamps

---

### D5 Attendance Records

Stores submitted attendance records.

Includes:

* Attendance record ID
* Event ID
* Name fields
* School/University
* Designation/Category
* Sex
* Email address
* Consent responses
* Optional signature data
* Attendance status
* Submission timestamp

---

### D6 Attendance Sheet Exports

Stores attendance sheet generation/download records.

Includes:

* Export ID
* Event ID
* Exported by
* Export format
* Total records
* File path, if stored
* Export timestamp

---

### D7 Audit Logs

Stores important system activity logs.

Includes:

* Audit log ID
* User ID, nullable for public/system events
* Action
* Entity type
* Entity ID
* Description
* Timestamp

---

## 4. Internal Processes

## 1.0 Authenticate Admin User

This process handles login and access verification for Super Admin and Program Admin users.

Input:

* Login credentials from Super Admin or Program Admin

Process:

* Validate credentials
* Check account status
* Identify user role
* Retrieve assigned programs if Program Admin

Data stores used:

* D1 Users
* D2 Roles and Program Assignments
* D7 Audit Logs

Output:

* Login result
* User session
* Role-based access information

---

## 2.0 Manage Users, Roles, Programs, and Assignments

This process handles admin users, program records, and Program Admin assignments.

Input:

* Admin account details
* Program details
* Program update requests
* Program archive requests
* Program Admin assignment requests

Process:

* Validate user/program details
* Save or update records
* Assign Program Admins to programs
* Apply access restrictions

Data stores used:

* D1 Users
* D2 Roles and Program Assignments
* D3 Programs
* D7 Audit Logs

Output:

* User records
* Program records
* Program assignment results

Important rule:

Only Super Admin can manage users and program assignments.

---

## 3.0 Manage Events

This process handles event creation and management under programs.

Input:

* Event details from Super Admin or Program Admin
* Event update requests
* Event status changes

Process:

* Validate event details
* Check program access
* Save event record
* Update event status
* Retrieve event list

Data stores used:

* D2 Roles and Program Assignments
* D3 Programs
* D4 Events
* D7 Audit Logs

Output:

* Event records
* Event list
* Event management result

Important rule:

Program Admin can manage events only under assigned programs.

---

## 4.0 Generate Attendance Link and QR Code

This process handles public attendance URL and QR code generation.

Input:

* Event ID
* QR generation request

Process:

* Verify event exists
* Check admin permission
* Generate or retrieve public attendance URL
* Generate QR code pointing to the public attendance URL
* Store QR code path/data

Data stores used:

* D4 Events
* D7 Audit Logs

Output:

* Public attendance link
* Generated QR code
* Updated event record

Important rule:

The QR code points to the system's attendance page, not to Google Forms.

---

## 5.0 Collect Attendance Submission

This process handles public attendee submissions.

Input:

* Event code or public attendance link
* Fixed attendance form data from External Attendee

Process:

* Check event exists
* Check event status is open
* Display fixed attendance page
* Receive submitted attendance fields
* Send submission for validation

Data stores used:

* D4 Events
* D5 Attendance Records

Output:

* Submitted attendance data
* Validation messages
* Submission confirmation

Important rule:

External Attendees do not log in.

---

## 6.0 Validate and Store Attendance Records

This process validates submitted attendance records before storing them.

Input:

* Submitted attendance data
* Event information

Process:

* Validate required fields
* Validate email format
* Validate consent values
* Check duplicate submissions within the same event
* Store valid records
* Flag duplicate or invalid records

Data stores used:

* D4 Events
* D5 Attendance Records
* D7 Audit Logs, for significant system/admin actions

Output:

* Stored attendance records
* Duplicate records
* Invalid records
* Validation result

Important rule:

Duplicate detection in the MVP should only be within the same event.

---

## 7.0 Generate Dashboard, Reports, and Attendance Sheets

This process generates dashboard summaries, reports, and template-based attendance sheets.

Input:

* Dashboard request
* Event report request
* Program report request
* Attendance sheet generation request
* Export request
* Fixed DICT attendance sheet layout, as an internal report format

Process:

* Retrieve program data
* Retrieve event data
* Retrieve attendance records
* Apply role-based filters
* Generate summary or report
* Generate attendance sheet using DICT template format
* Record download/export if requested

Data stores used:

* D2 Roles and Program Assignments
* D3 Programs
* D4 Events
* D5 Attendance Records
* D6 Attendance Sheet Exports
* D7 Audit Logs

Output:

* Dashboard summary
* Event attendance report
* Program summary report
* Downloadable attendance sheet
* Exported report

Important rule:

Program Admin reports and downloads must be limited to assigned programs/events only.

---

## 8.0 Manage Audit Trail

This process records and retrieves audit logs.

Input:

* System activity from major processes
* Audit log request from Super Admin

Process:

* Store important actions
* Retrieve audit logs
* Filter logs by date, user, action, or entity

Data stores used:

* D7 Audit Logs

Output:

* Audit log records
* Audit trail report

Important rule:

Only Super Admin should view full audit logs in the MVP.

---

## 5. Major Data Flow Summary

### Super Admin

Super Admin sends:

* Login credentials
* Program details
* User assignment details
* Event details
* Event status changes
* Attendance sheet generation requests
* Report requests

Super Admin receives:

* Login result
* Dashboard summary
* Program records
* Event records
* QR codes and public attendance links
* Attendance records
* Attendance sheets
* Reports
* Audit logs

---

### Program Admin

Program Admin sends:

* Login credentials
* Event details for assigned programs
* Event status changes
* QR/link generation requests
* Attendance sheet generation requests, if allowed
* Report requests

Program Admin receives:

* Login result
* Assigned programs
* Event records
* QR codes and public attendance links
* Attendance records for assigned events
* Attendance sheets for assigned events, if allowed
* Reports for assigned programs/events

---

### External Attendee

External Attendee sends:

* Attendance details to the system's public attendance page

External Attendee receives:

* Attendance page
* Validation messages
* Submission confirmation

---

### DICT Attendance Sheet Template

The template is not an external data source. It is a fixed output format implemented inside the report/attendance sheet generation logic.

The format defines:

* Required output layout
* Required columns
* Privacy notice section

The system produces:

* Generated attendance sheet for selected event

---

## 6. Critical Rules Reflected in DFD Level 1

1. External Attendees do not access the admin system.
2. Attendance is collected directly through the system.
3. Google Forms and CSV import are not part of the core MVP flow.
4. Program Admin access must be filtered by assigned programs.
5. Attendance records are linked to events.
6. Events are linked to programs.
7. The attendance sheet template is a fixed generated output format, not an external entity.
8. Audit logs are created for important admin actions.
9. Same-person detection across events is not part of MVP.
10. Duplicate detection is limited to the same event.
