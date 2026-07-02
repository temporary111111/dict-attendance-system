# DFD Level 0 / Context Diagram

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This DFD Level 0 shows the high-level data flow between the main system and its external entities.

The system manages DICT programs and events, generates public attendance links and QR codes, collects attendance through a fixed system attendance page, stores attendance records, generates downloadable attendance sheets using the DICT template, generates reports, and records audit logs.

Important update:

Google Forms and Google Sheets are no longer external entities in the MVP. Attendance is collected directly by the system.

---

## 2. Main Process

### Program and Event Attendance Monitoring and Reporting System

This is the main system being developed.

The system handles:

* Admin login
* Program management
* Event management
* Attendance link and QR code generation
* Fixed public attendance submission
* Attendance validation
* Attendance records management
* Attendance sheet generation
* Report generation
* Audit trail

---

## 3. External Entities

## 3.1 Super Admin

The Super Admin manages the overall system.

Data sent to the system:

* Login credentials
* Program details
* Admin account details
* Program Admin assignments
* Event details
* Event status changes
* Attendance sheet generation requests
* Report requests

Data received from the system:

* Login result
* Dashboard summary
* Program records
* Event records
* Generated attendance link and QR code
* Attendance records
* Downloadable attendance sheets
* Attendance reports
* Audit logs

---

## 3.2 Program Admin

The Program Admin manages events and attendance records under assigned programs only.

Data sent to the system:

* Login credentials
* Event details under assigned programs
* Event status changes for events under assigned programs
* QR code/link generation requests
* Attendance sheet generation requests
* Report requests

Data received from the system:

* Login result
* Assigned program list
* Event records
* Generated attendance link and QR code
* Attendance records for events under assigned programs
* Downloadable attendance sheets for events under assigned programs, if allowed
* Event/program reports for assigned scope

---

## 3.3 External Attendee

The External Attendee submits attendance details through the system's fixed public attendance page.

Data sent to the system:

* Name
* School/University
* Designation/Category
* Sex
* Email address
* Consent responses
* Signature, if required

Data received from the system:

* Public attendance page
* Validation messages
* Submission confirmation

Important:

The External Attendee does not log in to the admin system.

---

## 4. High-Level Data Flow Summary

1. Super Admin logs in and manages users, programs, events, reports, and audit logs.
2. Program Admin logs in and manages events under assigned programs.
3. Admin opens an event for attendance collection.
4. The system generates a public attendance link and QR code.
5. External Attendee scans the QR code or opens the link.
6. External Attendee submits attendance through the fixed system page.
7. The system validates and stores the attendance record.
8. Admin closes the event after attendance collection.
9. The system generates dashboard summaries and reports.
10. The system generates downloadable attendance sheets using the DICT template.
11. The system records important admin actions in the audit trail.

---

## 5. Attendance Sheet Template Note

The DICT attendance sheet template is not an external entity in the MVP. It is a fixed output format that the system follows when generating downloadable attendance sheets.

Implementation meaning:

* Admins do not import the template during normal system use.
* The system does not provide a template builder.
* Developers implement the generated attendance sheet layout based on the supervisor-provided sample.

---

## 6. Critical Rules Reflected in DFD Level 0

1. External Attendees do not have system accounts.
2. Attendance is submitted directly to the system.
3. Google Forms and CSV import are not part of the core MVP flow.
4. Program Admin access is limited to assigned programs.
5. Attendance records are linked to events.
6. Events are linked to programs.
7. The attendance sheet template is a fixed output/report format, not an external data source.
8. Audit logs are created for important admin actions.
