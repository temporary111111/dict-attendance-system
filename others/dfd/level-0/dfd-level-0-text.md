# DFD Level 0 / Context Diagram

## Program and Event Attendance Monitoring and Reporting System for DICT

## External Entities

### Super Admin
# DFD Level 0 / Context Diagram

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This DFD Level 0 shows the high-level data flow between the main system and its external entities.

The system manages DICT programs and events, stores Google Form links, generates QR codes, imports attendance responses, generates reports, and records audit logs.

For the MVP, Google Forms is used as the attendance collection tool. External attendees submit attendance through Google Forms, not directly through the system.

---

## 2. Main Process

### Program and Event Attendance Monitoring and Reporting System

This is the main system being developed.

The system handles:

* Admin login
* Program management
* Event management
* Google Form link management
* QR code generation
* Attendance response import
* Attendance validation
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
* Report requests

Data received from the system:

* Login result
* Dashboard summary
* Program records
* Event records
* Attendance reports
* Audit logs

---

## 3.2 Program Admin

The Program Admin manages events and attendance records for assigned programs only.

Data sent to the system:

* Login credentials
* Event details
* Google Form link
* Attendance CSV file
* Report requests

Data received from the system:

* Login result
* Assigned program list
* Event records
* Generated QR code
* Attendance import result
* Event/program reports

---

## 3.3 External Attendee

The External Attendee submits attendance details through Google Forms.

Data sent to Google Forms:

* Name
* Contact details
* Address details
* Consent response
* Event code, if included in the form

Data received:

* Google Form confirmation message

Important: The External Attendee does not log in to the system.

---

## 3.4 Google Forms / Google Sheets

Google Forms collects attendance responses from external attendees. Google Sheets or exported CSV files provide attendance data for import into the system.

Data received from the system/admin:

* Google Form link used for QR generation
* Event code, if pre-filled link is used

Data sent to the system:

* Attendance response data
* Response timestamp
* Submitted attendee details
* Exported CSV file or linked Google Sheet data

---

## 4. High-Level Data Flow Summary

1. Super Admin logs in and manages programs, users, events, and reports.
2. Program Admin logs in and manages events under assigned programs.
3. Program Admin attaches a Google Form link to an event.
4. The system generates a QR code pointing to the Google Form link.
5. External Attendee scans QR code and submits attendance through Google Forms.
6. Google Forms stores attendance responses.
7. Admin exports or syncs the attendance responses.
8. The system imports and validates attendance data.
9. The system generates dashboard summaries and reports.
10. The system records important admin actions in the audit trail.

The Super Admin manages system users, programs, events, reports, and audit logs.

### Program Admin

The Program Admin manages events and attendance records only for assigned programs.

### External Attendee

The External Attendee submits attendance details through Google Forms. The attendee does not have a system account.

### Google Forms / Google Sheets

Google Forms collects attendance responses from external attendees. Google Sheets or exported CSV files provide the attendance response data to the system.

---

## Main Process

### Program and Event Attendance Monitoring and Reporting System

The system manages DICT programs and events, stores Google Form links, generates QR codes, imports attendance responses, validates records, generates reports, and records audit logs.

---

## Data Flows

### Super Admin to System

* Login credentials
* Program details
* Admin account details
* Program Admin assignments
* Event details
* Report requests

### System to Super Admin

* Login result
* Dashboard summary
* Program records
* Event records
* Attendance reports
* Audit logs

### Program Admin to System

* Login credentials
* Event details
* Google Form link
* CSV attendance file
* Report requests

### System to Program Admin

* Login result
* Assigned program list
* Event list
* Generated QR code
* Attendance import results
* Event/program reports

### External Attendee to Google Forms

* Attendance details
* Name
* Contact information
* Address information
* Consent response

### Google Forms / Google Sheets to System

* Attendance response data
* Exported CSV file
* Response timestamp
* Submitted attendee details

### System to Google Form Link / QR

* Stored Google Form link
* Event code
* QR code pointing to the attendance form
