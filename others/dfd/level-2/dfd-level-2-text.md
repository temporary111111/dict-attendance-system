# DFD Level 2

## Processes 5.0, 6.0, and 7.0: Attendance Submission, Validation, Storage, and Sheet Generation

### Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This DFD Level 2 explains the detailed flow of attendance submission, validation, storage, and attendance sheet generation.

In the MVP, attendance is collected through the system's fixed public attendance page. The system no longer depends on Google Forms, Google Sheets, or CSV import for the core attendance flow.

This process covers:

* Opening a public event attendance link
* Checking event status
* Displaying the fixed attendance page
* Submitting attendance details
* Validating required fields
* Checking consent responses
* Detecting duplicate submissions within the same event
* Storing valid attendance records
* Flagging invalid or duplicate records
* Generating the official attendance sheet using the DICT template
* Recording export/download activity in the audit trail

---

## 2. Parent Processes

This Level 2 DFD expands the following DFD Level 1 processes:

### 5.0 Collect Attendance Submission

Handles public attendance page access and fixed attendance submission.

### 6.0 Validate and Store Attendance Records

Handles submission validation, duplicate checking, and database storage.

### 7.0 Generate Dashboard, Reports, and Attendance Sheets

Handles attendance sheet generation using the supervisor-provided DICT template.

---

## 3. External Entities

## 3.1 External Attendee

The External Attendee submits attendance through the public event attendance page.

## 3.2 Super Admin

The Super Admin may view all attendance records and generate/download attendance sheets for any event.

## 3.3 Program Admin

The Program Admin may view attendance records and generate/download attendance sheets only for events under assigned programs, if allowed by policy.

## 4. Data Stores

## D2 Roles and Program Assignments

Used to verify whether a Program Admin is allowed to view or generate records for the selected event.

## D4 Events

Stores event details, event code, public attendance URL, QR code path/data, and event status.

## D5 Attendance Records

Stores submitted attendance records.

## D6 Attendance Sheet Exports

Stores attendance sheet generation/download details.

## D7 Audit Logs

Stores attendance, report, and export-related activity logs.

---

## 5. Level 2 Processes

## 5.1 Open Public Attendance Link

External Attendee opens the event attendance link or scans the event QR code.

Input:

* Public attendance URL or event code

Process:

* Check if the event exists
* Check if the event is not archived
* Check if the event status is open
* If valid, display the fixed attendance page

Data store used:

* D4 Events

Output:

* Attendance page
* Event closed/invalid link message, if not allowed

---

## 5.2 Display Fixed Attendance Page

The system displays the fixed attendance form for the event.

Displayed fields:

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
* Signature, if required

Output:

* Fixed attendance form

Important rule:

Admins do not build or customize the attendance form in the MVP.

---

## 5.3 Submit Attendance Details

External Attendee submits the fixed attendance form.

Input:

* Event ID from public link
* Submitted attendance details

Process:

* Receive submitted fields
* Attach submission to selected event
* Send submission to validation process

Output:

* Submitted attendance data for validation

---

## 6.1 Validate Event Status

The system checks whether the selected event can accept attendance submissions.

Input:

* Event ID

Process:

* Retrieve event from D4 Events
* Check event status
* Allow only open events to accept attendance

Output:

* Event status valid
* Submission blocked if event is draft, closed, or archived

---

## 6.2 Validate Required Fields

The system validates each submitted attendance record.

Input:

* Submitted attendance data

Process:

* Check required fields
* Trim extra spaces
* Normalize basic text fields
* Check if consent responses were submitted

Recommended required fields:

* First Name
* Last Name
* School/University
* Designation/Category
* Sex
* Email Address
* Consent responses

Output:

* Valid row for further checking
* Invalid row with reason

---

## 6.3 Validate Contact Information

The system validates contact fields.

Input:

* Email address

Process:

* Check email format
* Normalize email casing
* Flag invalid email values

Output:

* Valid contact data
* Invalid contact data

Important rule:

For MVP, email should be the primary duplicate identifier.

---

## 6.4 Check Duplicate Within Same Event

The system checks whether the submission is a duplicate for the selected event.

Input:

* Event ID
* Email address

Process:

* Search D5 Attendance Records for an existing record with the same event and same email
* If match is found, mark submission as duplicate or possible duplicate based on policy

Data store used:

* D5 Attendance Records

Output:

* Unique submission
* Duplicate submission
* Possible duplicate submission

Important rule:

The MVP only checks duplicates within the same event. Cross-event same-person detection is not part of MVP.

---

## 6.5 Store Attendance Record

The system stores validated attendance records.

Input:

* Valid attendance submission
* Event ID

Process:

* Save attendance record to D5 Attendance Records
* Link attendance record to selected event
* Set status to valid, duplicate, invalid, or void as applicable
* Store submitted timestamp

Data store used:

* D5 Attendance Records

Output:

* Stored attendance record
* Updated attendance count

---

## 6.6 Show Submission Result

The system displays the result to the external attendee.

Output shown:

* Submission confirmation, if valid
* Duplicate or already-submitted message, if duplicate policy rejects the submission
* Field validation errors, if invalid

Important rule:

Do not expose other attendees' data in public messages.

---

## 7.1 Select Event for Attendance Sheet

Admin selects the event for attendance sheet generation.

Input:

* Selected event ID
* Admin user ID

Process:

* Check if the event exists
* Check if the user has permission to access the event
* If Program Admin, verify that the event belongs to an assigned program

Data stores used:

* D2 Roles and Program Assignments
* D4 Events

Output:

* Valid selected event
* Access denied message, if unauthorized

---

## 7.2 Retrieve Attendance Records

The system retrieves attendance records for the selected event.

Input:

* Event ID

Process:

* Retrieve event details
* Retrieve valid attendance records
* Exclude void records from official count by default
* Include duplicate/invalid records only if admin selects an audit/review view

Data stores used:

* D4 Events
* D5 Attendance Records

Output:

* Attendance record list
* Total valid attendance count

---

## 7.3 Format Records Using DICT Template

The system maps stored attendance fields into the required template columns.

Input:

* Event details
* Attendance records
* Fixed DICT attendance sheet layout rules

Process:

* Add event title, venue, and date
* Add DICT heading and privacy notice
* Combine separated name fields into the template's Name column
* Map school/university
* Map designation/category
* Map sex into F/M columns
* Map email address
* Map consent responses into checkbox columns
* Map signature data if available
* Paginate rows as needed

Output:

* Formatted attendance sheet content

---

## 7.4 Generate Downloadable File

The system generates the attendance sheet file.

Input:

* Formatted attendance sheet content
* Requested export format

Process:

* Generate PDF, Excel, or other approved format
* Store file path if the system keeps generated files
* Count exported records

Data store used:

* D6 Attendance Sheet Exports

Output:

* Downloadable attendance sheet
* Export record

---

## 7.5 Record Audit Log

The system records the attendance sheet generation/download activity.

Input:

* Admin user ID
* Event ID
* Export ID
* Export summary

Process:

* Create audit log entry
* Include action type: GENERATE_ATTENDANCE_SHEET or DOWNLOAD_ATTENDANCE_SHEET
* Include affected event and export record

Data store used:

* D7 Audit Logs

Output:

* Audit log record

---

## 6. Main Data Flow Summary

1. External attendee opens event attendance link or scans QR code.
2. System checks event status.
3. System displays fixed attendance page.
4. External attendee submits attendance details.
5. System validates required fields and email.
6. System checks duplicates within the same event.
7. System stores valid attendance record.
8. System shows submission result.
9. Admin selects event for attendance sheet generation.
10. System verifies admin access.
11. System retrieves event attendance records.
12. System formats records using the fixed DICT attendance sheet layout.
13. System generates downloadable attendance sheet.
14. System records export/download in audit trail.

---

## 7. Critical Rules

1. Public attendance submission is allowed only for open events.
2. Program Admin can only view/generate attendance sheets for assigned program events.
3. External attendees do not log in.
4. The attendance form is fixed, not dynamically built per event.
5. Invalid submissions should not be silently saved as valid records.
6. Duplicate submissions should not overwrite existing attendance records.
7. Name-only duplicate checking should not be trusted.
8. All attendance sheet generation/download actions must be logged.
9. Valid attendance records must always be linked to an event.
10. Generated attendance sheets must follow the supervisor-provided DICT template format.
11. The DICT template is a fixed output format, not an external entity or runtime import.

---

## 8. Recommended Clarifications

Before implementation, confirm:

* Should digital signature be captured, or should the signature column remain blank?
* Should email be strictly required?
* Should mobile number be collected even though it is not in the template?
* Is PSGC/address collection still required even though the template has no address columns?
* Should Program Admins be allowed to download official attendance sheets?
