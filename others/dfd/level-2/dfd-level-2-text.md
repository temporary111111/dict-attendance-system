# DFD Level 2

## Processes 5.0, 6.0, and 7.0: Attendance Submission, Review, and Sheet Generation

### Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This DFD Level 2 explains the detailed flow of attendance submission,
validation, storage, admin review, and attendance sheet generation.

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
* Rejecting invalid or exact duplicate public submissions
* Searching and viewing stored attendance records
* Reviewing attendance status with a required reason
* Generating the official attendance sheet using the DICT template
* Recording export/download activity in the audit trail

---

## 2. Parent Processes

This Level 2 DFD expands the following DFD Level 1 processes:

### 5.0 Collect Attendance Submission

Handles public attendance page access and fixed attendance submission.

### 6.0 Validate, Store, and Review Attendance Records

Handles submission validation, duplicate checking, database storage, and
authorized admin attendance review.

### 7.0 Generate Dashboard, Reports, and Attendance Sheets

Handles attendance sheet generation using the supervisor-provided DICT template.

---

## 3. External Entities

## 3.1 External Attendee

The External Attendee submits attendance through the public event attendance page.

## 3.2 Super Admin

The Super Admin may view all attendance records, update their status, and
generate/download attendance sheets for any event.

## 3.3 Program Admin

The Program Admin may view, update attendance status, and generate attendance
sheets only for events under actively assigned programs.

## 4. Data Stores

## D2 Roles and Program Assignments

Used to verify whether a Program Admin is actively assigned before viewing,
reviewing, or generating records for the selected event.

## D4 Event Configuration

Stores event details, event code, public attendance URL, QR code path/data,
event status, and the event's fixed-field requirement snapshot.

## D5 Attendance Records

Stores submitted attendance records.

## D6 Attendance Sheet Exports

Stores attendance sheet generation/download details.

## D7 Audit Logs

Stores attendance status changes, report actions, and export-related activity
logs.

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

The system displays the fixed attendance form and marks fields using the
event's required/optional settings.

Displayed fields:

* First Name
* Middle Name
* Last Name
* Suffix
* Affiliation (school, university, agency, office, company, LGU, or organization)
* Designation/Category
* Sex
* Email Address
* Consent for photo/video/audio documentation and possible DICT publication
* Consent to be included in the organizer's database for future processing of relevant documents
* PSGC-based address
* Typed signature or uploaded signature image

Output:

* Fixed attendance form

Important rule:

Admins do not build or customize the attendance form in the MVP. They can only
change whether approved configurable fields are required or optional.

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

* Check fields required by the event configuration
* Trim extra spaces
* Normalize basic text fields
* Check if consent responses were submitted

Always-required fields:

* First Name
* Last Name
* Email Address
* Database-processing consent

Affiliation, designation/category, sex, documentation/publication consent,
middle name, suffix, signature, and address fields follow the selected event's
configuration. A required documentation/publication consent needs an answer,
but an explicit decline is valid.

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
* If a match is found, reject the repeated public submission

Data store used:

* D5 Attendance Records

Output:

* Unique submission
* Duplicate rejection

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
* Set a newly accepted record's status to valid
* Keep the separate duplicate review flag available for later admin review
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

## 6.7 Review Attendance Record Status

An authorized admin searches, views, and reviews stored attendance records.

Input:

* Event ID or attendance record ID
* Optional search text and attendance status filter
* Requested new status and required reason for a change
* Current admin user and role

Process:

* Verify that the event and attendance record exist
* Allow Super Admin access to any record
* For Program Admin, verify an active assignment to the record's program
* Return a paginated list or complete record detail
* Return a signature image only through the protected endpoint
* Update the status to valid, duplicate, invalid, or void when requested
* Create an audit log containing the old status, new status, and reason
* Commit the status and audit log in one database transaction

Data stores used:

* D2 Roles and Program Assignments
* D4 Events
* D5 Attendance Records
* D7 Audit Logs

Output:

* Paginated attendance records
* Attendance record detail
* Status update result
* Access-denied or not-found result

Important rules:

* A Program Admin must have an active assignment to the related program.
* Repeating the current status does not create another audit log.
* Status review does not freely edit attendee-submitted fields and does not hard delete the record.
* The separate `duplicate_flag` is not automatically changed by a status update.

---

## 7.1 Select Event for Attendance Sheet

Admin selects the event for attendance sheet generation.

Input:

* Selected event ID
* Admin user ID

Process:

* Check if the event exists
* Check if the user has permission to access the event
* If Program Admin, verify an active assignment to the event's program
* Allow generation for draft, open, closed, and archived events

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
* Retrieve all valid attendance records from the selected event only
* Exclude duplicate, invalid, and void records from the PDF and official count
* Order records chronologically for stable row numbering

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
* Map affiliation to the general Affiliation column
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
* Fixed PDF export format

Process:

* Generate a landscape A4 PDF in memory
* Return the PDF directly with private, non-cacheable headers
* Keep the export file path null because the server retains no PDF copy
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
* Include action type: generated_attendance_sheet
* Include affected event and export record

Data store used:

* D7 Audit Logs

Output:

* Audit log record

---

## 8. Main Data Flow Summary

1. External attendee opens event attendance link or scans QR code.
2. System checks event status.
3. System displays fixed attendance page.
4. External attendee submits attendance details.
5. System validates required fields and email.
6. System checks duplicates within the same event.
7. System stores valid attendance record.
8. System shows submission result.
9. Admin searches or opens stored attendance records.
10. System verifies role and active program assignment.
11. Admin may submit a new attendance status with a reason.
12. System saves the actual status change and audit log together.
13. Admin selects event for attendance sheet generation.
14. System verifies admin access and retrieves event attendance records.
15. System formats records using the fixed DICT attendance sheet layout.
16. System generates the downloadable attendance sheet.
17. System records export/download in the audit trail.

---

## 9. Critical Rules

1. Public attendance submission is allowed only for open events.
2. Program Admin can only view or review records for actively assigned program events.
3. External attendees do not log in.
4. The attendance form has fixed fields; only approved required/optional settings vary per event.
5. Invalid submissions should not be silently saved as valid records.
6. Duplicate submissions should not overwrite existing attendance records.
7. Name-only duplicate checking should not be trusted.
8. All attendance sheet generation/download actions must be logged.
9. Valid attendance records must always be linked to an event.
10. Generated attendance sheets must follow the supervisor-provided DICT template format.
11. The DICT template is a fixed output format, not an external entity or runtime import.
12. An actual attendance status change requires a reason and an audit log in the same transaction.
13. Submitted attendee details are not freely edited or hard deleted in the MVP.
14. Uploaded signature images are private and require authenticated, role-based access.
15. One generated PDF represents one selected event and all of its valid attendees.
16. Event status does not block an authorized attendance-sheet export.
17. The server records export/audit history but does not retain generated PDF files.

---

## 10. Resolved Attendance Decisions

The current attendance workflow uses these approved decisions:

* Email is required.
* Signature is optional by default and may be required by the selected event.
* First name, last name, email, and database-processing consent are always required.
* Mobile number is not collected in the MVP.
* PSGC address collection is optional, but supplied address codes must form a valid hierarchy.
* Super Admin can review all records.
* Program Admin can review records only under actively assigned programs.
* Program Admin can generate attendance sheets only for actively assigned program events.
