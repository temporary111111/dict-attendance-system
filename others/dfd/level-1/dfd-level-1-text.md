# DFD Level 1

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This DFD Level 1 shows the major internal processes of the system and how data flows between external entities, system processes, and data stores.

Unlike DFD Level 0, which shows the system as one whole process, DFD Level 1 breaks the system into core functions.

---

## 2. External Entities

The external entities remain the same as DFD Level 0:

1. Super Admin
2. Program Admin
3. External Attendee
4. Google Forms / Google Sheets

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
* Google Form link
* Event code
* QR code path
* Status
* Timestamps

---

### D5 Attendance Records

Stores imported attendance records.

Includes:

* Attendance record ID
* Event ID
* Response timestamp
* Name fields
* Contact details
* Address details
* Attendance status
* Import batch ID

---

### D6 Attendance Import Batches

Stores import transaction details.

Includes:

* Import batch ID
* Event ID
* Imported by
* Source filename
* Total rows
* Successful rows
* Duplicate rows
* Failed rows
* Import timestamp

---

### D7 Audit Logs

Stores important system activity logs.

Includes:

* Audit log ID
* User ID
* Action
* Entity type
* Entity ID
* Description
* Timestamp

---

### D8 PSGC Reference Data

Stores PSGC-related address reference data.

Includes:

* Regions
* Provinces
* Cities/Municipalities
* Barangays
* PSGC codes

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

## 2.0 Manage Programs

This process handles creation, updating, viewing, and archiving of programs.

Input:

* Program details from Super Admin
* Program update requests
* Program archive requests

Process:

* Validate program details
* Save or update program records
* Retrieve program list
* Apply access restrictions

Data stores used:

* D3 Programs
* D2 Roles and Program Assignments
* D7 Audit Logs

Output:

* Program records
* Program list
* Program management result

Important rule:

Super Admin can manage all programs. Program Admin can only view assigned programs.

---

## 3.0 Manage Program Admin Assignments

This process handles assigning Program Admins to programs.

Input:

* User assignment request from Super Admin
* Selected Program Admin
* Selected program

Process:

* Validate selected user
* Validate selected program
* Save assignment
* Update access scope

Data stores used:

* D1 Users
* D2 Roles and Program Assignments
* D3 Programs
* D7 Audit Logs

Output:

* Updated program assignment
* Assignment confirmation

Important rule:

Only Super Admin can assign Program Admins.

---

## 4.0 Manage Events

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

* D3 Programs
* D4 Events
* D2 Roles and Program Assignments
* D7 Audit Logs

Output:

* Event records
* Event list
* Event management result

Important rule:

Program Admin can manage events only under assigned programs.

---

## 5.0 Manage Google Form Link and QR Code

This process handles Google Form link storage and QR code generation.

Input:

* Google Form link from admin
* Event code
* QR generation request

Process:

* Validate Google Form link
* Attach link to event
* Generate QR code pointing to the Google Form link
* Store QR code path/data

Data stores used:

* D4 Events
* D7 Audit Logs

Output:

* Generated QR code
* Attendance link
* Updated event record

Important rule:

For the MVP, the system does not automatically create Google Forms. It only stores the link and generates QR codes.

---

## 6.0 Import Attendance Responses

This process handles importing attendance responses from Google Forms or Google Sheets.

Input:

* Attendance CSV file from Super Admin or Program Admin
* Attendance response data from Google Forms / Google Sheets
* Selected event

Process:

* Validate selected event
* Read imported file
* Check required columns
* Create import batch
* Send rows for validation

Data stores used:

* D4 Events
* D6 Attendance Import Batches
* D7 Audit Logs

Output:

* Parsed attendance rows
* Import batch record
* Import summary

Important rule:

For the MVP, CSV import is the safest initial method.

---

## 7.0 Validate and Store Attendance Records

This process validates imported attendance records before storing them.

Input:

* Parsed attendance rows from import process
* Event information
* PSGC reference data

Process:

* Validate required fields
* Validate email/mobile format
* Validate PSGC address fields
* Check duplicate entries within the same event
* Store valid records
* Flag duplicate or invalid records

Data stores used:

* D5 Attendance Records
* D6 Attendance Import Batches
* D8 PSGC Reference Data
* D7 Audit Logs

Output:

* Stored attendance records
* Duplicate records
* Invalid records
* Validation result

Important rule:

Duplicate detection in the MVP should only be within the same event.

---

## 8.0 Generate Dashboard and Reports

This process generates dashboard summaries and reports.

Input:

* Dashboard request
* Event report request
* Program report request
* Export request

Process:

* Retrieve program data
* Retrieve event data
* Retrieve attendance records
* Apply role-based filters
* Generate summary or report
* Export report if requested

Data stores used:

* D3 Programs
* D4 Events
* D5 Attendance Records
* D6 Attendance Import Batches
* D2 Roles and Program Assignments
* D7 Audit Logs

Output:

* Dashboard summary
* Event attendance report
* Program summary report
* Exported report

Important rule:

Program Admin reports must be limited to assigned programs only.

---

## 9.0 Manage Audit Trail

This process records and retrieves audit logs.

Input:

* System activity from all major processes
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
* Google Form links
* Import files
* Report requests

Super Admin receives:

* Login result
* Dashboard summary
* Program records
* Event records
* QR codes
* Import results
* Reports
* Audit logs

---

### Program Admin

Program Admin sends:

* Login credentials
* Event details for assigned programs
* Google Form links
* Attendance CSV files
* Report requests

Program Admin receives:

* Login result
* Assigned programs
* Event records
* QR codes
* Import results
* Reports for assigned programs/events

---

### External Attendee

External Attendee sends:

* Attendance details to Google Forms

External Attendee receives:

* Google Form confirmation

---

### Google Forms / Google Sheets

Google Forms / Google Sheets sends:

* Attendance response data
* Exported CSV file
* Response timestamp
* Submitted attendee details

Google Forms / Google Sheets receives:

* Attendance submissions from External Attendees

---

## 6. Critical Rules Reflected in DFD Level 1

1. External Attendees do not directly access the admin system.
2. Google Forms is treated as an external system.
3. Attendance responses enter the system through import or sync.
4. Program Admin access must be filtered by assigned programs.
5. Attendance records are linked to events.
6. Events are linked to programs.
7. Audit logs are created for important admin actions.
8. Same-person detection across events is not part of MVP.
9. Duplicate detection is limited to the same event.
10. The system stores and reports attendance data after import.
