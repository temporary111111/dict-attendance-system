# User Roles and Permissions Matrix

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This document defines the access permissions of each user role in the system. The goal is to ensure that users can only access the features and data they are authorized to use.

The system will use Role-Based Access Control (RBAC). Each admin user will be assigned a role, and each role will determine what actions the user can perform.

Updated scope:

* Attendance is collected through the system's fixed public attendance page.
* Google Forms and CSV import are not part of the core MVP flow.
* The supervisor-provided attendance sheet is a downloadable report/output template.

---

## 2. User Roles

The MVP will support three main user categories:

1. Super Admin
2. Program Admin
3. External Attendee

Only Super Admin and Program Admin users can log in to the admin system. External Attendees do not have accounts and only submit attendance through the public event attendance page.

---

## 3. Role Descriptions

## 3.1 Super Admin

The Super Admin has full access to the system.

The Super Admin is responsible for:

* Managing admin users
* Managing all programs
* Assigning Program Admins to programs
* Managing all events
* Configuring fixed attendance field requirements for all draft or open events
* Generating event attendance links and QR codes
* Viewing all attendance records
* Generating and downloading official attendance sheets
* Generating reports
* Exporting reports
* Viewing audit logs
* Managing system-wide records

The Super Admin can access all programs and all events.

---

## 3.2 Program Admin

The Program Admin has limited access based on assigned programs.

The Program Admin is responsible for:

* Managing events under assigned programs
* Configuring fixed attendance field requirements for assigned draft or open events
* Opening and closing attendance collection for events under assigned programs
* Generating QR codes and public attendance links for events under assigned programs
* Viewing attendance records under assigned programs
* Generating attendance sheets for events under actively assigned programs
* Generating reports for assigned programs and their events

The Program Admin must not access programs, events, attendance records, reports, or downloads outside their assigned programs.

---

## 3.3 External Attendee

The External Attendee is a person who attends a DICT program or event.

The External Attendee:

* Does not have a login account
* Does not access the admin system
* Opens the event attendance page through a QR code or public link
* Submits attendance details through the fixed system attendance page

---

## 4. Permissions Matrix

| Module / Feature                         | Super Admin | Program Admin                 | External Attendee        |
| ---------------------------------------- | ----------: | -----------------------------:| -----------------------: |
| Log in to admin system                   | Yes         | Yes                           | No                       |
| Log out of admin system                  | Yes         | Yes                           | No                       |
| View dashboard                           | Yes         | Limited                       | No                       |
| View all dashboard data                  | Yes         | No                            | No                       |
| View assigned program dashboard data     | Yes         | Yes                           | No                       |
| Create admin users                       | Yes         | No                            | No                       |
| Edit admin users                         | Yes         | No                            | No                       |
| Activate/deactivate admin users          | Yes         | No                            | No                       |
| Assign Program Admins to programs        | Yes         | No                            | No                       |
| Create programs                          | Yes         | No                            | No                       |
| View all programs                        | Yes         | No                            | No                       |
| View assigned programs                   | Yes         | Yes                           | No                       |
| Edit all programs                        | Yes         | No                            | No                       |
| Edit assigned programs                   | Yes         | No                            | No                       |
| Archive programs                         | Yes         | No                            | No                       |
| Create events                            | Yes         | Yes, assigned programs only   | No                       |
| View all events                          | Yes         | No                            | No                       |
| View assigned program events             | Yes         | Yes                           | No                       |
| Edit all events                          | Yes         | No                            | No                       |
| Edit assigned program events             | Yes         | Yes                           | No                       |
| Archive all events                       | Yes         | No                            | No                       |
| Archive assigned program events          | Yes         | No, close only by default     | No                       |
| Open/close event attendance status       | Yes         | Yes, events under assigned programs only | No              |
| Generate public attendance link          | Yes         | Yes, events under assigned programs only | No              |
| Generate QR code                         | Yes         | Yes, events under assigned programs only | No              |
| Submit attendance                        | No          | No                            | Yes, public page only    |
| View all attendance records              | Yes         | No                            | No                       |
| View assigned program event attendance records | Yes   | Yes                           | No                       |
| Edit attendance records                  | Restricted  | Restricted or No              | No                       |
| Delete attendance records                | No, void only | No                          | No                       |
| Mark attendance as valid/duplicate/invalid/void | Yes   | Yes, events under assigned programs only | No           |
| Generate all attendance sheets           | Yes         | No                            | No                       |
| Generate assigned program event attendance sheet | Yes | Yes, assigned programs only   | No                       |
| Download all attendance sheets           | Yes         | No                            | No                       |
| Download assigned attendance sheets      | Yes         | Yes, assigned programs only   | No                       |
| View reports for all programs            | Yes         | No                            | No                       |
| View reports for assigned programs       | Yes         | Yes                           | No                       |
| Export all reports                       | Yes         | No                            | No                       |
| Export assigned program reports          | Yes         | Yes, if allowed by policy     | No                       |
| View audit logs                          | Yes         | No or limited                 | No                       |
| Access system settings                   | Yes         | No                            | No                       |

---

## 5. Recommended MVP Permission Decisions

To avoid confusion during implementation, the following decisions are recommended for the MVP.

## 5.1 Program Creation

Only the Super Admin should create programs.

Reason:

Program records are high-level records. If every Program Admin can create programs, the system may become inconsistent.

Recommended rule:

* Super Admin: can create programs
* Program Admin: cannot create programs

---

## 5.2 Program Editing

Program Admins should not edit core program details by default.

Reason:

Program Admins are assigned to manage events under programs, not necessarily define the program itself.

Recommended rule:

* Super Admin: can edit program details
* Program Admin: can view assigned program details but cannot edit program details

---

## 5.3 Event Creation

Program Admins should be allowed to create events under their assigned programs.

Reason:

This is part of their operational role.

Recommended rule:

* Super Admin: can create events under any program
* Program Admin: can create events only under assigned programs

---

## 5.4 Event Editing

Program Admins may edit events under assigned programs.

Recommended rule:

* Super Admin: can edit all events
* Program Admin: can edit events under assigned programs only

Fields Program Admins may edit:

* Event title
* Event description
* Venue
* Event date
* Event status, if allowed by policy

Both admin roles may also change configurable fixed attendance fields between
required and optional while an accessible event is draft or open. They cannot
change the locked required fields or create a custom form.

---

## 5.5 Event Archiving

Program Admins may close events under assigned programs, but event archiving should be limited.

Recommended stricter rule:

* Super Admin: can archive events
* Program Admin: can close events but cannot archive them

This reduces accidental hiding of important records.

---

## 5.6 Attendance Link and QR Code

Program Admins should be allowed to generate attendance links and QR codes for events under assigned programs.

Recommended rule:

* Super Admin: can generate links and QR codes for all events
* Program Admin: can generate links and QR codes for events under assigned programs only

Important rule:

The generated QR code points to the system's public attendance page for the event.

---

## 5.7 Attendance Record Editing

Attendance records should not be freely editable.

Reason:

Attendance records are official operational records. If admins can casually edit them, the reports become less trustworthy.

Recommended MVP rule:

* Attendance records should be viewable.
* Editing should be restricted.
* If correction is needed, the record should be marked as void/invalid or corrected through a controlled process.
* Any correction must be logged in the audit trail.

Approved MVP permission:

* Super Admin: can mark any record as valid, duplicate, invalid, or void.
* Program Admin: can mark records only for events under actively assigned programs.
* External Attendee: no access after submission
* Every status change requires a reason and must be saved in the audit trail.
* Neither admin role can freely edit submitted attendee fields in the MVP.

---

## 5.8 Attendance Deletion

Hard deletion should not be allowed for attendance records in the MVP.

Recommended rule:

* Do not permanently delete attendance records.
* Use status such as valid, duplicate, invalid, or void.
* Keep audit logs for any status changes.

---

## 5.9 Attendance Sheet Download

The downloadable attendance sheet contains personal information, consent responses, and typed or image signatures.

Recommended rule:

* Super Admin: can generate and download attendance sheets for all events
* Program Admin: can generate and download attendance sheets only for events under actively assigned programs
* All downloads must be recorded in the audit trail
* Event status does not block an authorized attendance-sheet export

---

## 5.10 Report Export

Report export should be controlled because reports may contain personal information.

Recommended rule:

* Super Admin: can export all reports
* Program Admin: can export reports only for assigned programs and their events, if allowed
* Export actions must be recorded in the audit trail

---

## 5.11 Audit Log Access

Only Super Admin should view the full audit trail in the MVP.

Reason:

Audit logs may contain sensitive system activity details.

Recommended rule:

* Super Admin: full audit log access
* Program Admin: no audit log access in MVP, or limited view of own actions only in Phase 2

---

## 6. Data Access Rules

## 6.1 Super Admin Data Access

The Super Admin can access:

* All programs
* All events
* All attendance records
* All attendance sheet downloads/exports
* All reports
* All audit logs
* All admin users

---

## 6.2 Program Admin Data Access

A Program Admin can access only:

* Programs assigned to them
* Events under assigned programs
* Attendance records under events in assigned programs
* Attendance sheets under events in actively assigned programs
* Reports under assigned programs and their events

A Program Admin must not access:

* Unassigned programs
* Events under unassigned programs
* Attendance records from events outside assigned programs
* Attendance sheets from events outside assigned programs
* Reports from unassigned programs
* Admin account management
* Full audit trail

---

## 6.3 External Attendee Data Access

External Attendees do not access stored system data.

They only submit attendance through the public event attendance page.

---

## 7. RBAC Implementation Notes

RBAC should be enforced in both:

1. User interface
2. Backend/server-side logic

Hiding buttons in the UI is not enough.

Example:

Even if the Program Admin cannot see the Edit Event button, the backend must still block unauthorized requests if the Program Admin tries to access the endpoint directly.

---

## 8. Required Authorization Checks

Every protected admin action should check:

1. Is the user logged in?
2. Is the user active?
3. What is the user's role?
4. If Program Admin, is the program assigned to this user?
5. If accessing an event, does the event belong to an assigned program?
6. If accessing attendance records, do the records belong to an event under an assigned program?
7. If generating/downloading an attendance sheet, does the event belong to an assigned program?

Public attendance submission should check:

1. Does the event code/link exist?
2. Is the event open?
3. Is the event archived?
4. Is the submitted data valid?
5. Does the submission look like a duplicate for the same event?

---

## 9. Example Access Rules

## 9.1 Program Admin viewing an event

Allowed only if:

* User role is Program Admin
* Event belongs to a program assigned to that Program Admin

Otherwise, deny access.

---

## 9.2 Program Admin opening attendance collection

Allowed only if:

* User role is Program Admin
* Selected event belongs to an assigned program
* Event is not archived

Otherwise, deny access.

---

## 9.3 External attendee submitting attendance

Allowed only if:

* Public event link is valid
* Event status is open
* Submission passes validation

Otherwise, reject or show an appropriate message.

---

## 9.4 Super Admin downloading event attendance sheet

Allowed if:

* User role is Super Admin
* Event exists

---

## 9.5 Program Admin downloading event attendance sheet

Allowed only if:

* User role is Program Admin
* Event belongs to a program assigned to that Program Admin
* Program assignment is active

---

## 10. Recommended MVP Role Policy

For the MVP, use this stricter setup:

### Super Admin

Can do everything.

### Program Admin

Can:

* View assigned programs
* Create events under assigned programs
* Edit events under assigned programs
* Generate QR codes and attendance links for events under assigned programs
* Open/close events under assigned programs
* View attendance records for events under assigned programs
* Generate attendance sheets for events under actively assigned programs
* Generate reports for assigned programs and their events
* Export assigned reports, if allowed

Cannot:

* Create programs
* Archive programs
* Manage admin users
* Assign Program Admins
* View unassigned programs or events outside assigned programs
* Delete attendance records
* View full audit logs
* Change system settings

### External Attendee

Can only submit attendance through the public event attendance page.

---

## 11. Audit Requirements by Role

The system should log the following actions:

| Action                              | Logged for Super Admin | Logged for Program Admin |
| ----------------------------------- | ---------------------: | -----------------------: |
| Login                               | Yes                    | Yes                      |
| Logout                              | Yes                    | Yes                      |
| Create program                      | Yes                    | Not applicable           |
| Update program                      | Yes                    | Not applicable           |
| Archive program                     | Yes                    | Not applicable           |
| Assign Program Admin                | Yes                    | Not applicable           |
| Create event                        | Yes                    | Yes                      |
| Update event                        | Yes                    | Yes                      |
| Configure attendance requirements  | Yes                    | Yes, assigned programs only |
| Open event attendance               | Yes                    | Yes                      |
| Close event attendance              | Yes                    | Yes                      |
| Archive event                       | Yes                    | No                       |
| Generate attendance link / QR code  | Yes                    | Yes                      |
| Generate/download attendance sheet  | Yes                    | Yes, assigned programs only |
| Export report                       | Yes                    | Yes, if allowed          |
| Mark attendance status              | Yes                    | Yes, assigned programs only |

Public attendee submissions may also be logged as system events, but audit logs should not expose unnecessary personal data.

---

## 12. Final RBAC Principle

The system must follow this rule:

A user should only have access to the minimum features and data necessary to perform their assigned role.

For the MVP, strict access control is better than flexible but risky access.
