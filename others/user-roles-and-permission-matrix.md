# User Roles and Permissions Matrix

## Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This document defines the access permissions of each user role in the system. The goal is to ensure that users can only access the features and data they are authorized to use.

The system will use Role-Based Access Control (RBAC). Each admin user will be assigned a role, and each role will determine what actions the user can perform.

---

## 2. User Roles

The MVP will support three main user categories:

1. Super Admin
2. Program Admin
3. External Attendee

Only Super Admin and Program Admin users can log in to the system. External Attendees do not have accounts and only submit attendance through Google Forms.

---

## 3. Role Descriptions

## 3.1 Super Admin

The Super Admin has full access to the system.

The Super Admin is responsible for:

* Managing admin users
* Managing all programs
* Assigning Program Admins to programs
* Managing all events
* Viewing all attendance records
* Importing attendance responses
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
* Attaching Google Form links to assigned events
* Generating QR codes for assigned events
* Importing attendance records for assigned events
* Viewing attendance records under assigned programs
* Generating reports for assigned programs/events

The Program Admin must not access programs, events, attendance records, or reports outside their assigned programs.

---

## 3.3 External Attendee

The External Attendee is a person who attends a DICT program or event.

The External Attendee:

* Does not have a login account
* Does not access the admin system
* Only opens the Google Form through a QR code or link
* Submits attendance details through Google Forms

---

## 4. Permissions Matrix

| Module / Feature                       |           Super Admin |                Program Admin |         External Attendee |
| -------------------------------------- | --------------------: | ---------------------------: | ------------------------: |
| Log in to admin system                 |                   Yes |                          Yes |                        No |
| Log out of admin system                |                   Yes |                          Yes |                        No |
| View dashboard                         |                   Yes |                      Limited |                        No |
| View all dashboard data                |                   Yes |                           No |                        No |
| View assigned program dashboard data   |                   Yes |                          Yes |                        No |
| Create admin users                     |                   Yes |                           No |                        No |
| Edit admin users                       |                   Yes |                           No |                        No |
| Activate/deactivate admin users        |                   Yes |                           No |                        No |
| Assign Program Admins to programs      |                   Yes |                           No |                        No |
| Create programs                        |                   Yes | No, unless allowed by policy |                        No |
| View all programs                      |                   Yes |                           No |                        No |
| View assigned programs                 |                   Yes |                          Yes |                        No |
| Edit all programs                      |                   Yes |                           No |                        No |
| Edit assigned programs                 |                   Yes |   Maybe, depending on policy |                        No |
| Archive programs                       |                   Yes |                           No |                        No |
| Create events                          |                   Yes |  Yes, assigned programs only |                        No |
| View all events                        |                   Yes |                           No |                        No |
| View assigned program events           |                   Yes |                          Yes |                        No |
| Edit all events                        |                   Yes |                           No |                        No |
| Edit assigned program events           |                   Yes |                          Yes |                        No |
| Archive all events                     |                   Yes |                           No |                        No |
| Archive assigned program events        |                   Yes |    Yes, if allowed by policy |                        No |
| Attach Google Form link                |                   Yes |    Yes, assigned events only |                        No |
| Update Google Form link                |                   Yes |    Yes, assigned events only |                        No |
| Generate QR code                       |                   Yes |    Yes, assigned events only |                        No |
| Open/close event attendance status     |                   Yes |    Yes, assigned events only |                        No |
| Submit attendance                      |                    No |                           No | Yes, through Google Forms |
| Import attendance responses            |                   Yes |    Yes, assigned events only |                        No |
| View all attendance records            |                   Yes |                           No |                        No |
| View assigned event attendance records |                   Yes |                          Yes |                        No |
| Edit attendance records                |            Restricted |             Restricted or No |                        No |
| Delete attendance records              | No, archive/void only |                           No |                        No |
| Mark attendance as void/invalid        |                   Yes |  Maybe, assigned events only |                        No |
| View reports for all programs          |                   Yes |                           No |                        No |
| View reports for assigned programs     |                   Yes |                          Yes |                        No |
| Export all reports                     |                   Yes |                           No |                        No |
| Export assigned program reports        |                   Yes |    Yes, if allowed by policy |                        No |
| View audit logs                        |                   Yes |                No or limited |                        No |
| Manage PSGC reference data             |                   Yes |                           No |                        No |
| Access system settings                 |                   Yes |                           No |                        No |

---

## 5. Recommended MVP Permission Decisions

To avoid confusion during implementation, the following decisions are recommended for the MVP.

## 5.1 Program Creation

Only the Super Admin should create programs.

Reason:

Program records are high-level records. If every Program Admin can create programs, the system may become messy and inconsistent.

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

Optional future rule:

Program Admins may edit limited fields only, such as program description or remarks, if approved by office policy.

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
* Program Admin: can edit assigned events only

Fields Program Admins may edit:

* Event title
* Event description
* Venue
* Event date
* Google Form link
* Google Sheet link, if used
* Event status

---

## 5.5 Event Archiving

Program Admins may archive events only if the office allows it.

Sa MVP, safer kung Super Admin lang muna ang final archive authority.

Recommended stricter rule:

* Super Admin: can archive events
* Program Admin: can close events but cannot archive them

This reduces accidental hiding of important records.

---

## 5.6 Attendance Record Editing

Attendance records should not be freely editable.

Reason:

Attendance records are official operational records. If admins can casually edit them, the reports become less trustworthy.

Recommended MVP rule:

* Imported attendance records should be viewable.
* Editing should be restricted.
* If correction is needed, record should be marked as void/invalid or corrected through a controlled process.
* Any correction must be logged in the audit trail.

Recommended permission:

* Super Admin: can mark records as void/invalid
* Program Admin: can request or flag issues, but not directly delete records
* External Attendee: no access

---

## 5.7 Attendance Deletion

Hard deletion should not be allowed for attendance records in the MVP.

Recommended rule:

* Do not permanently delete attendance records.
* Use status such as valid, duplicate, invalid, or void.
* Keep audit logs for any status changes.

This is safer for real office use.

---

## 5.8 Report Export

Report export should be controlled because reports may contain personal information.

Recommended rule:

* Super Admin: can export all reports
* Program Admin: can export reports only for assigned programs/events, if allowed
* Export actions must be recorded in the audit trail

---

## 5.9 Audit Log Access

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
* All reports
* All audit logs
* All admin users

---

## 6.2 Program Admin Data Access

A Program Admin can access only:

* Programs assigned to them
* Events under assigned programs
* Attendance records under assigned events
* Reports under assigned programs/events

A Program Admin must not access:

* Unassigned programs
* Events under unassigned programs
* Attendance records from unassigned events
* Reports from unassigned programs
* Admin account management
* Full audit trail

---

## 6.3 External Attendee Data Access

External Attendees do not access stored system data.

They only submit attendance through the Google Form link provided for the event.

---

## 7. RBAC Implementation Notes

RBAC should be enforced in both:

1. User interface
2. Backend/server-side logic

Hiding buttons in the UI is not enough.

Example:

Even if the Program Admin cannot see the “Edit Program” button, the backend must still block unauthorized requests if the Program Admin tries to access the endpoint directly.

---

## 8. Required Authorization Checks

Every protected action should check:

1. Is the user logged in?
2. Is the user active?
3. What is the user’s role?
4. If Program Admin, is the program assigned to this user?
5. If accessing an event, does the event belong to an assigned program?
6. If accessing attendance records, do the records belong to an assigned event/program?

---

## 9. Example Access Rules

## 9.1 Program Admin viewing an event

Allowed only if:

* User role is Program Admin
* Event belongs to a program assigned to that Program Admin

Otherwise, deny access.

---

## 9.2 Program Admin importing attendance

Allowed only if:

* User role is Program Admin
* Selected event belongs to assigned program
* Event is not archived

Otherwise, deny access.

---

## 9.3 Super Admin exporting program report

Allowed if:

* User role is Super Admin
* Program exists

---

## 9.4 Program Admin exporting program report

Allowed only if:

* User role is Program Admin
* Program is assigned to that Program Admin
* Export permission is enabled for Program Admins

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
* Attach/update Google Form links for assigned events
* Generate QR codes for assigned events
* Open/close assigned events
* Import attendance responses for assigned events
* View attendance records for assigned events
* Generate reports for assigned programs/events
* Export assigned reports, if allowed

Cannot:

* Create programs
* Archive programs
* Manage admin users
* Assign Program Admins
* View unassigned programs/events
* Delete attendance records
* View full audit logs
* Change system settings

### External Attendee

Can only submit attendance through Google Forms.

---

## 11. Audit Requirements by Role

The system should log the following actions:

| Action                         | Logged for Super Admin | Logged for Program Admin |
| ------------------------------ | ---------------------: | -----------------------: |
| Login                          |                    Yes |                      Yes |
| Logout                         |                    Yes |                      Yes |
| Create program                 |                    Yes |           Not applicable |
| Update program                 |                    Yes |           Not applicable |
| Archive program                |                    Yes |           Not applicable |
| Assign Program Admin           |                    Yes |           Not applicable |
| Create event                   |                    Yes |                      Yes |
| Update event                   |                    Yes |                      Yes |
| Close event                    |                    Yes |                      Yes |
| Archive event                  |                    Yes |               If allowed |
| Attach/update Google Form link |                    Yes |                      Yes |
| Generate QR code               |                    Yes |                      Yes |
| Import attendance records      |                    Yes |                      Yes |
| Export report                  |                    Yes |                      Yes |
| Mark attendance invalid/void   |                    Yes |               If allowed |

---

## 12. Final RBAC Principle

The system must follow this rule:

A user should only have access to the minimum features and data necessary to perform their assigned role.

For the MVP, strict access control is better than flexible but risky access.
