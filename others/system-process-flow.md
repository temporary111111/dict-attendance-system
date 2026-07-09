# System Process Flow

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This process flow explains how the system will work from program creation up to attendance sheet generation and reporting.

The system is intended for DICT program/event attendance monitoring. It is not an employee daily time-in/time-out system. External attendees will not have system accounts. The system will collect attendance through a fixed public attendance page and will generate downloadable attendance sheets based on the DICT template provided by the supervisor.

Important scope update:

* Google Forms is no longer part of the MVP.
* CSV import is no longer the primary attendance flow.
* The system will not include a form builder.
* The supervisor-provided attendance sheet is the downloadable output/report template.

---

## 2. Main System Workflow

The basic workflow is:

1. Super Admin logs in.
2. Super Admin creates a program.
3. Super Admin assigns Program Admins to the program.
4. Program Admin or Super Admin creates an event under the program.
5. Admin opens the event for attendance collection.
6. System generates a public attendance link and QR code for the event.
7. External attendee scans the QR code or opens the link.
8. External attendee submits attendance through the fixed system attendance page.
9. System validates and stores the attendance record in MySQL.
10. Admin monitors attendance records while the event is open.
11. Admin closes the event after attendance collection is finished.
12. Admin generates and downloads the official attendance sheet using the DICT template.
13. Admin views dashboard and reports per event/program.
14. System records important actions in the audit trail.

---

## 3. Super Admin Process Flow

## 3.1 Super Admin Login

1. Super Admin opens the system.
2. Super Admin enters login credentials.
3. System checks if the account exists.
4. System verifies the password.
5. System checks if the account is active.
6. System identifies the user role as Super Admin.
7. System redirects the user to the Super Admin dashboard.
8. System records the login action in the audit trail.

---

## 3.2 Create Program

1. Super Admin opens the Program Management module.
2. Super Admin selects Add Program.
3. System displays the program form.
4. Super Admin enters program details:
   * Program name
   * Description
   * Owning organizational unit
   * Status
5. System validates required fields.
6. System saves the program to the database.
7. System records the action in the audit trail.
8. System displays the newly created program.

---

## 3.3 Assign Program Admin

1. Super Admin opens a specific program.
2. Super Admin selects Assign Program Admin.
3. System displays available admin users.
4. Super Admin selects one or more Program Admins.
5. System saves the program assignment.
6. Program Admin gains access only to that assigned program.
7. System records the assignment in the audit trail.

Important rule:

Program Admins should not automatically access all programs. Their access must be based on program assignment.

---

## 4. Program Admin Process Flow

## 4.1 Program Admin Login

1. Program Admin opens the system.
2. Program Admin enters login credentials.
3. System verifies the account.
4. System checks if the account is active.
5. System identifies the user role as Program Admin.
6. System retrieves only the programs assigned to that user.
7. System redirects the user to the Program Admin dashboard.
8. System records the login action in the audit trail.

---

## 4.2 View Assigned Programs

1. Program Admin opens the dashboard.
2. System displays only assigned programs.
3. Program Admin selects a program.
4. System displays events under that selected program.

Important rule:

If the Program Admin tries to open an unassigned program directly through the URL, the system must deny access.

---

## 5. Event Management Process Flow

## 5.1 Create Event

1. Super Admin or Program Admin opens a program.
2. User selects Add Event.
3. System checks permission:
   * Super Admin can create events under any program.
   * Program Admin can create events only under assigned programs.
4. System displays the event form.
5. User enters event details:
   * Event title
   * Event description
   * Venue
   * Event date
6. System generates or accepts an event code.
7. System validates required fields.
8. System saves the event under the selected program.
9. System records the action in the audit trail.

---

## 5.2 Generate Attendance Link and QR Code

1. Admin opens the event details page.
2. Admin selects Generate Attendance Link or Generate QR Code.
3. System verifies that the event exists and that the user has access.
4. System creates a public attendance URL for the event.
5. System generates a QR code pointing to the public attendance URL.
6. System stores the public attendance URL and QR code reference.
7. Admin can view, download, or print the QR code.
8. System records the QR generation action in the audit trail.

Important rule:

The QR code points to the system's public attendance page, not to Google Forms.

---

## 5.3 Set Event Status

An event may have statuses such as:

* Draft
* Open
* Closed
* Archived

Process:

1. Admin opens the event.
2. Admin changes event status.
3. System validates permission.
4. System saves the new status.
5. System records the status change in the audit trail.

Recommended rules:

* Draft: Event is being prepared.
* Open: Attendance collection is active.
* Closed: Attendance collection is finished; reports and downloads are available.
* Archived: Event is hidden from normal active views but kept for records.

---

## 6. External Attendee Process Flow

## 6.1 Open Attendance Page

1. External attendee scans the QR code or opens the public attendance link.
2. System checks if the event exists.
3. System checks if the event status is open.
4. System displays the fixed attendance page for the event.

Fixed attendance fields:

* First Name
* Middle Name
* Last Name
* Suffix
* School/University
* Designation/Category
* Sex
* Email Address
* Address using PSGC codes, if required by office policy
* Consent for photo/video/audio documentation and possible DICT publication
* Consent to be included in the organizer's database for future processing of relevant documents
* Signature, if digital signature capture is required by the office

Important rule:

External attendees do not log in to the system.

---

## 6.2 Submit Attendance

1. External attendee fills out the fixed attendance page.
2. External attendee submits the form.
3. System validates required fields.
4. System validates email format.
5. System checks consent responses.
6. System checks duplicate submissions within the same event.
7. System saves valid attendance record to MySQL.
8. System flags possible duplicate records if needed.
9. System shows a confirmation message.

Important rule:

Attendance records are stored directly by the system. There is no Google Forms export/import step in the MVP.

---

## 7. Attendance Validation Rules

During attendance submission, the system should check:

* Required fields are not empty.
* Email format is valid.
* Sex field has a valid value.
* Consent values are recorded.
* Event status is open.
* Duplicate entries within the same event are flagged.

Duplicate checking for MVP:

* Same event + same email = duplicate or possible duplicate.

Name-only matching should not be used as the main duplicate check because different people can have the same or similar names.

Cross-event same-person detection should be Phase 2, not MVP.

---

## 8. Attendance Records Process Flow

## 8.1 View Attendance Records

1. Admin opens a program.
2. Admin selects an event.
3. System displays attendance records for that event.
4. Admin can search or filter records.
5. Program Admin can only view records under assigned programs.
6. Super Admin can view all attendance records.

---

## 8.2 Handling Invalid or Duplicate Records

Recommended MVP behavior:

1. System flags duplicate or invalid records during submission.
2. Admin reviews flagged records.
3. Admin may mark a record as:
   * Valid
   * Duplicate
   * Invalid
   * Void
4. System records any status change in the audit trail.

Important rule:

Avoid hard deleting attendance records. Use status fields instead.

---

## 9. Attendance Sheet Generation Process Flow

## 9.1 Generate Event Attendance Sheet

1. Admin opens the event details page or Reports module.
2. Admin selects Generate Attendance Sheet.
3. System verifies that the admin has access to the event.
4. System retrieves valid attendance records for the selected event.
5. System formats the records using the DICT attendance sheet template.
6. System includes:
   * DICT heading
   * Event title
   * Venue
   * Event date
   * Privacy notice
   * Attendance table
7. System paginates attendance rows as needed.
8. Admin downloads the generated file.
9. System records the download/export action in the audit trail.

The attendance sheet should include the following columns:

* Row number
* Name
* School/University
* Designation/Category
* Sex: F/M
* Email Address
* Address using PSGC codes, if required by office policy
* Consent for photo/video/audio documentation and possible publication
* Consent for organizer database/future processing
* Signature

Important rule:

The downloaded attendance sheet is the template-based output. It is not a dynamic form builder.

---

## 9.2 Program Report

1. Admin opens Reports module.
2. Admin selects a program.
3. System retrieves all events under that program.
4. System summarizes attendance records per event.
5. System generates program report.

The program report should include:

* Program name
* Owning organizational unit
* Number of events
* Attendance count per event
* Total attendance records
* Date range, if applicable

6. Admin may export the report.
7. System records the export action in the audit trail.

---

## 10. Dashboard Process Flow

## 10.1 Super Admin Dashboard

After login, the Super Admin dashboard should display:

* Total programs
* Total events
* Total attendance records
* Recent created events
* Recent attendance submissions
* Recent audit activities
* Attendance count per program

Super Admin sees system-wide data.

---

## 10.2 Program Admin Dashboard

After login, the Program Admin dashboard should display only assigned program data:

* Assigned programs
* Events under assigned programs
* Attendance count per event under assigned programs
* Recent attendance submissions under events in assigned programs

Program Admin must not see global system totals unless filtered only to their assigned programs.

---

## 11. Audit Trail Process Flow

For every important action, the system should automatically create an audit log.

Actions to log:

* Login
* Logout
* Create program
* Update program
* Archive program
* Assign Program Admin
* Create event
* Update event
* Open event attendance
* Close event attendance
* Archive event
* Generate QR code
* Submit attendance, as a system event
* Generate/download attendance sheet
* Export report
* Mark attendance as invalid/duplicate/void
* Activate/deactivate admin account

Each audit log should contain:

* User who performed the action, if an admin action
* Action performed
* Affected module/entity
* Affected record ID, if applicable
* Description
* Date and time
* Optional IP address
* Optional user agent

---

## 12. Error and Exception Process Flow

## 12.1 Invalid Login

1. User enters invalid credentials.
2. System rejects login.
3. System displays a safe error message.
4. System does not reveal whether the email or password is wrong.

Recommended message:

Invalid credentials. Please try again.

---

## 12.2 Unauthorized Access

1. Program Admin attempts to access an unassigned program/event.
2. System checks permissions.
3. System blocks access.
4. System displays Access denied.
5. System may log the unauthorized attempt.

---

## 12.3 Closed or Archived Event

1. External attendee opens the attendance link.
2. System checks event status.
3. If the event is closed or archived, system blocks new submission.
4. System displays a safe message that attendance submission is no longer available.

---

## 12.4 Duplicate Submission

1. External attendee submits attendance.
2. System checks for an existing record with the same event and email.
3. If match is found, system flags or rejects the duplicate based on policy.
4. System does not silently overwrite the existing record.

---

## 12.5 Invalid Attendance Submission

1. External attendee submits incomplete or invalid data.
2. System validates required fields and email format.
3. System displays field-level errors.
4. System does not save incomplete data as a valid attendance record.

---

## 13. Critical System Rules

## Rule 1: External Attendees Have No Accounts

External attendees only submit attendance through the public event attendance page.

---

## Rule 2: Programs Contain Events

A program can have multiple events.

An event must belong to one program.

---

## Rule 3: Attendance Records Belong to Events

Each attendance record must be linked to a specific event.

---

## Rule 4: Program Admin Access Is Limited

Program Admins can only access assigned programs and related events/records.

---

## Rule 5: The System Collects Attendance Directly

The system's public attendance page is the MVP collection layer.

---

## Rule 6: No Form Builder in MVP

The attendance page uses fixed fields based on the required DICT attendance format.

---

## Rule 7: Generate Template-Based Attendance Sheets

The official event attendance sheet is generated after or during the event using stored attendance records and the supervisor-provided template format.

---

## Rule 8: Do Not Hard Delete Attendance Records

Attendance records should be marked as valid, duplicate, invalid, or void instead of being permanently deleted.

---

## Rule 9: Audit Trail Is Required

Important admin actions must be logged.

---

## 14. Recommended MVP End-to-End Scenario

Example:

1. Super Admin logs in.
2. Super Admin creates a program called Digital Literacy Training.
3. Super Admin assigns Juan as Program Admin.
4. Juan logs in.
5. Juan sees only Digital Literacy Training.
6. Juan creates an event called Day 1 Orientation.
7. Juan opens the event for attendance collection.
8. System generates a QR code and public attendance link.
9. Juan displays the QR code.
10. Attendees scan the QR code.
11. Attendees submit attendance through the fixed system page.
12. System validates and stores attendance records.
13. Juan monitors attendance records.
14. Juan closes the event after attendance collection.
15. Juan generates the DICT attendance sheet.
16. Juan downloads the attendance sheet.
17. System logs all important actions in the audit trail.

---

## 15. Summary

The system process should stay simple and operational for the MVP.

The MVP should focus on:

* Admin login
* Program and event management
* Event public attendance link and QR code generation
* Fixed system attendance submission
* Attendance validation
* Template-based attendance sheet generation
* Reports
* RBAC
* Audit trail

The system should not start with advanced features such as dynamic form builder, same-person detection across events, Google Forms integration, biometric attendance, or advanced analytics. Those can be future enhancements after the core workflow is stable.
