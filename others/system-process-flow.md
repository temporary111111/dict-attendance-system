# System Process Flow

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This process flow explains how the system will work from program creation up to attendance reporting.

The system is intended for DICT program/event attendance monitoring. It is not an employee daily time-in/time-out system. External attendees will not have system accounts. For the MVP, attendance responses will be collected through Google Forms, then imported or synced into the system for validation, reporting, and record management.

---

## 2. Main System Workflow

The basic workflow is:

1. Super Admin logs in.
2. Super Admin creates a program.
3. Super Admin assigns Program Admins to the program.
4. Program Admin or Super Admin creates an event under the program.
5. Admin attaches the Google Form link to the event.
6. System generates a QR code for the Google Form link.
7. External attendee scans the QR code or opens the link.
8. External attendee submits attendance through Google Forms.
9. Admin imports the Google Form responses into the system.
10. System validates and stores attendance records.
11. Admin views dashboard and generates reports.
12. System records important actions in the audit trail.

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
2. Super Admin selects “Add Program.”
3. System displays the program form.
4. Super Admin enters program details:

   * Program name
   * Description
   * Office/division
   * Status
5. System validates required fields.
6. System saves the program to the database.
7. System records the action in the audit trail.
8. System displays the newly created program.

---

## 3.3 Assign Program Admin

1. Super Admin opens a specific program.
2. Super Admin selects “Assign Program Admin.”
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
2. User selects “Add Event.”
3. System checks permission:

   * Super Admin can create events under any program.
   * Program Admin can create events only under assigned programs.
4. System displays the event form.
5. User enters event details:

   * Event title
   * Event description
   * Venue
   * Event date
   * Google Form link
6. System generates or accepts an event code.
7. System validates required fields.
8. System saves the event under the selected program.
9. System records the action in the audit trail.

---

## 5.2 Attach or Update Google Form Link

1. Admin opens the event details page.
2. Admin enters or updates the Google Form link.
3. System validates that the link is not empty and follows a valid URL format.
4. System saves the Google Form link.
5. System records the update in the audit trail.

Important rule:

For the MVP, the system stores and manages the Google Form link. It does not automatically create the Google Form unless Google Forms API or Apps Script integration is added later.

---

## 5.3 Generate QR Code

1. Admin opens the event details page.
2. Admin selects “Generate QR Code.”
3. System checks if the event has a valid Google Form link.
4. System generates a QR code pointing to the Google Form link.
5. System stores the QR code path or QR data.
6. Admin can view, download, or print the QR code.
7. System records the QR generation action in the audit trail.

Recommended improvement:

Use a pre-filled Google Form link containing the event code, so the attendance response can be matched to the correct event more reliably.

---

## 5.4 Set Event Status

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
* Closed: Attendance collection is finished, but reports are still available.
* Archived: Event is hidden from normal active views but kept for records.

---

## 6. External Attendee Process Flow

## 6.1 Open Attendance Form

1. External attendee scans the QR code or opens the attendance link.
2. The link opens the assigned Google Form.
3. External attendee fills out the attendance form.

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

## 6.2 Submit Attendance

1. External attendee submits the Google Form.
2. Google Forms stores the response.
3. The response becomes available in Google Forms or linked Google Sheets.
4. The system does not immediately receive the response unless automatic sync is implemented.
5. For MVP, admin will import the response data manually through CSV or similar file export.

Important rule:

External attendees do not log in to the system. Their only interaction is through the Google Form.

---

## 7. Attendance Import Process Flow

For MVP, the recommended method is CSV import from Google Forms or Google Sheets.

## 7.1 Export Responses from Google Forms/Sheets

1. Admin opens the Google Form or linked Google Sheet.
2. Admin exports the responses as CSV.
3. Admin downloads the CSV file.
4. Admin opens the system and selects the related event.

---

## 7.2 Import Attendance CSV

1. Admin opens the event details page.
2. Admin selects “Import Attendance.”
3. System displays the import page.
4. Admin uploads the CSV file.
5. System reads the CSV columns.
6. System checks if required columns are present.
7. System validates each row.
8. System imports valid records.
9. System flags invalid or duplicate records.
10. System displays import summary.
11. System records the import action in the audit trail.

---

## 7.3 Import Validation Rules

During import, the system should check:

* Required fields are not empty.
* Event code matches the selected event, if event code exists.
* Email format is valid, if email is provided.
* Mobile number format is valid, if mobile number is provided.
* PSGC fields are valid or match available PSGC reference data.
* Duplicate entries within the same event are flagged.

---

## 7.4 Duplicate Checking for MVP

The system should only detect duplicates within the same event.

Recommended rules:

* Same event + same email = duplicate or possible duplicate.
* Same event + same mobile number = duplicate or possible duplicate.

Name-only matching should not be used as the main duplicate check because different people can have the same or similar names.

Cross-event same-person detection should be Phase 2, not MVP.

---

## 7.5 Import Result Summary

After import, the system should show:

* Total rows found
* Successfully imported rows
* Duplicate rows
* Invalid rows
* Failed rows
* Import date and time
* Imported by

The system should store this in an import batch record.

---

## 8. Attendance Records Process Flow

## 8.1 View Attendance Records

1. Admin opens a program.
2. Admin selects an event.
3. System displays imported attendance records for that event.
4. Admin can search or filter records.
5. Program Admin can only view records under assigned programs.
6. Super Admin can view all attendance records.

---

## 8.2 Handling Invalid or Duplicate Records

Recommended MVP behavior:

1. System flags duplicate or invalid records during import.
2. Admin reviews the flagged records.
3. Admin may mark a record as:

   * Valid
   * Duplicate
   * Invalid
   * Void
4. System records any status change in the audit trail.

Important rule:

Avoid hard deleting attendance records. Use status fields instead.

---

## 9. Report Generation Process Flow

## 9.1 Event Report

1. Admin opens Reports module.
2. Admin selects a specific event.
3. System retrieves attendance records for that event.
4. System generates event attendance report.

The event report should include:

* Program name
* Event title
* Event date
* Venue
* Total attendance count
* Attendee list
* Name fields
* Contact fields, if allowed
* Address fields
* Submission timestamp

5. Admin may export the report.
6. System records the export action in the audit trail.

---

## 9.2 Program Report

1. Admin opens Reports module.
2. Admin selects a program.
3. System retrieves all events under that program.
4. System summarizes attendance records per event.
5. System generates program report.

The program report should include:

* Program name
* Office/division
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
* Recent imports
* Recent audit activities
* Attendance count per program

Super Admin sees system-wide data.

---

## 10.2 Program Admin Dashboard

After login, the Program Admin dashboard should display only assigned program data:

* Assigned programs
* Events under assigned programs
* Attendance count per assigned event
* Recent imports under assigned events

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
* Change event status
* Attach/update Google Form link
* Generate QR code
* Import attendance
* Export report
* Mark attendance as invalid/duplicate/void
* Activate/deactivate admin account

Each audit log should contain:

* User who performed the action
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

“Invalid credentials. Please try again.”

---

## 12.2 Unauthorized Access

1. Program Admin attempts to access an unassigned program/event.
2. System checks permissions.
3. System blocks access.
4. System displays “Access denied.”
5. System may log the unauthorized attempt.

---

## 12.3 Missing Google Form Link

1. Admin attempts to generate QR code.
2. System checks if Google Form link exists.
3. If missing, system blocks QR generation.
4. System asks admin to attach a valid Google Form link first.

---

## 12.4 Invalid CSV Import

1. Admin uploads a CSV file.
2. System checks required columns.
3. If required columns are missing, import is rejected.
4. System displays the missing columns.
5. System does not import incomplete data.

---

## 12.5 Duplicate Records

1. System detects duplicate based on event + email or event + mobile number.
2. System flags duplicate record.
3. System does not silently overwrite the existing record.
4. Admin can review duplicate records.

---

## 13. Critical System Rules

## Rule 1: External Attendees Have No Accounts

External attendees only submit attendance through Google Forms.

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

## Rule 5: Google Forms Is the MVP Collection Layer

The system manages the event and reporting workflow. Google Forms collects the attendance responses.

---

## Rule 6: CSV Import Is the MVP Data Entry Method

Automatic Google Sheets sync can be added later, but should not be required for the MVP.

---

## Rule 7: Do Not Hard Delete Attendance Records

Attendance records should be marked as valid, duplicate, invalid, or void instead of being permanently deleted.

---

## Rule 8: Audit Trail Is Required

Important admin actions must be logged.

---

## 14. Recommended MVP End-to-End Scenario

Example:

1. Super Admin logs in.
2. Super Admin creates a program called “Digital Literacy Training.”
3. Super Admin assigns Juan as Program Admin.
4. Juan logs in.
5. Juan sees only “Digital Literacy Training.”
6. Juan creates an event called “Day 1 Orientation.”
7. Juan attaches the Google Form link for Day 1 Orientation.
8. System generates a QR code.
9. Juan prints or displays the QR code.
10. Attendees scan the QR code.
11. Attendees submit the Google Form.
12. Juan exports responses from Google Forms/Sheets as CSV.
13. Juan uploads the CSV to the system under “Day 1 Orientation.”
14. System validates and imports attendance records.
15. System flags duplicates or invalid rows.
16. Juan views the event attendance report.
17. Juan exports the report.
18. System logs all important actions in the audit trail.

---

## 15. Summary

The system process should stay simple and operational for the MVP.

The MVP should focus on:

* Admin login
* Program and event management
* Google Form link and QR code handling
* CSV import of attendance responses
* Attendance validation
* Reports
* RBAC
* Audit trail

The system should not start with advanced features such as same-person detection across events, custom form builder, automatic Google Forms creation, or biometric attendance. Those are future enhancements after the core workflow is stable.
