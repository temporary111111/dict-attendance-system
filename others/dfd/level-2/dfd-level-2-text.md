# DFD Level 2

## Process 6.0 and 7.0: Import, Validate, and Store Attendance Responses

### Program and Event Attendance Monitoring and Reporting System for DICT

## 1. Purpose

This DFD Level 2 explains the detailed flow of attendance response import and validation.

In the MVP, attendance responses are collected through Google Forms and imported into the system using CSV export from Google Forms or Google Sheets.

This process covers:

* Selecting the event
* Uploading the CSV file
* Reading the response data
* Validating required fields
* Checking event code
* Checking PSGC/address data
* Detecting duplicate submissions within the same event
* Storing valid attendance records
* Flagging invalid or duplicate records
* Recording import batch details
* Logging the import activity in the audit trail

---

## 2. Parent Processes

This Level 2 DFD expands the following DFD Level 1 processes:

### 6.0 Import Attendance Responses

Handles file upload, event selection, CSV reading, and import batch creation.

### 7.0 Validate and Store Attendance Records

Handles row validation, duplicate checking, PSGC validation, and database storage.

---

## 3. External Entities

## 3.1 Super Admin

The Super Admin may import attendance responses for any event.

## 3.2 Program Admin

The Program Admin may import attendance responses only for events under assigned programs.

## 3.3 Google Forms / Google Sheets

Google Forms / Google Sheets provides exported attendance response data through CSV.

---

## 4. Data Stores

## D2 Roles and Program Assignments

Used to verify whether a Program Admin is allowed to import attendance for the selected event.

## D4 Events

Stores event details, event code, Google Form link, and event status.

## D5 Attendance Records

Stores valid imported attendance records.

## D6 Attendance Import Batches

Stores import transaction details such as filename, total rows, successful rows, failed rows, duplicate rows, and imported by.

## D7 Audit Logs

Stores import-related activity logs.

## D8 PSGC Reference Data

Stores official PSGC address reference data used to validate region, province, city/municipality, and barangay information.

---

## 5. Level 2 Processes

## 6.1 Select Event for Import

Admin selects the event where attendance responses will be imported.

Input:

* Selected event
* Admin user ID

Process:

* Check if the event exists
* Check if the event is not archived
* Check if the user has permission to access the event
* If Program Admin, verify that the event belongs to an assigned program

Data stores used:

* D2 Roles and Program Assignments
* D4 Events

Output:

* Valid selected event
* Access denied message, if unauthorized

---

## 6.2 Upload Attendance CSV File

Admin uploads the CSV file exported from Google Forms or Google Sheets.

Input:

* CSV file
* Selected event ID
* Admin user ID

Process:

* Check if file is uploaded
* Check file type
* Check file size, if limit is implemented
* Temporarily read the file for processing

Output:

* Uploaded CSV file data
* File upload error, if invalid

---

## 6.3 Read and Parse CSV Data

The system reads the uploaded CSV file.

Input:

* Uploaded CSV file

Process:

* Read CSV headers
* Read CSV rows
* Convert rows into structured data
* Count total rows

Output:

* Parsed attendance rows
* CSV header list
* Total row count

---

## 6.4 Validate CSV Format

The system checks if the CSV has the required columns.

Required columns should include:

* Timestamp
* Event Code, if used
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
* Data Privacy Consent

Process:

* Compare CSV headers with expected fields
* Identify missing columns
* Reject import if critical columns are missing

Output:

* Valid CSV structure
* Missing column errors

Important rule:

If critical columns are missing, the system should stop the import before saving records.

---

## 6.5 Create Import Batch Record

The system creates an import batch record before storing attendance records.

Input:

* Event ID
* Imported by
* Source filename
* Total rows

Process:

* Create import batch
* Set initial counts:

  * successful rows = 0
  * failed rows = 0
  * duplicate rows = 0

Data store used:

* D6 Attendance Import Batches

Output:

* Import batch ID

---

## 7.1 Validate Required Fields Per Row

The system validates each attendance row.

Input:

* Parsed attendance row

Process:

* Check required fields
* Trim extra spaces
* Normalize basic text fields
* Check if consent was given
* Check if at least one contact field exists, if required by policy

Possible required fields:

* First Name
* Last Name
* Mobile Number or Email Address
* Region
* Province
* City/Municipality
* Barangay
* Data Privacy Consent

Output:

* Valid row for further checking
* Invalid row with reason

---

## 7.2 Validate Event Code

The system verifies whether the imported row belongs to the selected event.

Input:

* Event code from row
* Selected event ID

Process:

* Retrieve expected event code from D4 Events
* Compare row event code with selected event code
* If event code does not match, flag the row

Data store used:

* D4 Events

Output:

* Event code valid
* Event code mismatch

Important rule:

If event code is not used in the Google Form, this validation can be skipped. However, using event code is recommended.

---

## 7.3 Validate Contact Information

The system validates contact fields.

Input:

* Email address
* Mobile number

Process:

* Check email format, if email is provided
* Check mobile number format, if mobile number is provided
* Normalize mobile number format if possible
* Flag invalid contact values

Output:

* Valid contact data
* Invalid contact data

Important rule:

For MVP, email or mobile number should be used for duplicate checking. Name-only duplicate detection is weak.

---

## 7.4 Validate PSGC Address Data

The system validates address fields against PSGC reference data.

Input:

* Region
* Province
* City/Municipality
* Barangay

Process:

* Check if region exists in PSGC reference data
* Check if province belongs to selected region
* Check if city/municipality belongs to selected province
* Check if barangay belongs to selected city/municipality

Data store used:

* D8 PSGC Reference Data

Output:

* Valid PSGC address
* Invalid PSGC address
* Address mismatch warning

Important note:

If Google Forms collects address names instead of PSGC codes, the system may need mapping or manual review. PSGC code-based input is cleaner but harder to implement using plain Google Forms.

---

## 7.5 Check Duplicate Within Same Event

The system checks whether the row is a duplicate for the selected event.

Input:

* Event ID
* Email address
* Mobile number

Process:

* Search D5 Attendance Records for existing record with same event and same email
* Search D5 Attendance Records for existing record with same event and same mobile number
* If match is found, mark row as duplicate or possible duplicate

Data store used:

* D5 Attendance Records

Output:

* Unique row
* Duplicate row
* Possible duplicate row

Important rule:

The MVP only checks duplicates within the same event. Cross-event same-person detection is not part of MVP.

---

## 7.6 Store Valid Attendance Record

The system stores validated attendance records.

Input:

* Valid attendance row
* Event ID
* Import batch ID

Process:

* Save attendance record to D5 Attendance Records
* Link attendance record to selected event
* Link attendance record to import batch
* Set status to valid

Data store used:

* D5 Attendance Records

Output:

* Stored attendance record
* Updated successful row count

---

## 7.7 Flag Invalid or Duplicate Rows

The system handles rows that cannot be imported as valid records.

Input:

* Invalid row
* Duplicate row
* Validation error reason

Process:

* Mark row as invalid or duplicate
* Store reason if error tracking table is implemented
* Update failed or duplicate row count

Data stores used:

* D6 Attendance Import Batches
* Optional import error records table

Output:

* Invalid row summary
* Duplicate row summary

Recommended optional table:

* attendance_import_errors

This table can store row number, error type, and error message.

---

## 7.8 Update Import Batch Summary

After processing all rows, the system updates the import batch summary.

Input:

* Total rows
* Successful rows
* Duplicate rows
* Failed rows

Process:

* Update D6 Attendance Import Batches
* Store final import status

Data store used:

* D6 Attendance Import Batches

Output:

* Final import summary

---

## 7.9 Display Import Result

The system displays the import result to the admin.

Output shown:

* Total rows
* Successfully imported rows
* Duplicate rows
* Invalid rows
* Failed rows
* Error messages, if any

---

## 7.10 Record Audit Log

The system records the import activity.

Input:

* Admin user ID
* Event ID
* Import batch ID
* Import summary

Process:

* Create audit log entry
* Include action type: IMPORT_ATTENDANCE
* Include affected event and import batch

Data store used:

* D7 Audit Logs

Output:

* Audit log record

---

## 6. Main Data Flow Summary

1. Admin selects event.
2. System verifies access permission.
3. Admin uploads CSV file.
4. System reads and validates CSV format.
5. System creates import batch.
6. System validates each row.
7. System checks event code.
8. System validates contact information.
9. System validates PSGC address data.
10. System checks duplicates within the same event.
11. System stores valid records.
12. System flags duplicate and invalid rows.
13. System updates import batch summary.
14. System displays import result.
15. System records audit log.

---

## 7. Critical Rules

1. Program Admin can only import attendance for assigned program events.
2. Archived events should not accept new imports unless allowed by Super Admin.
3. CSV files must match the expected format.
4. Critical missing columns should stop the import.
5. Invalid rows should not be silently saved as valid records.
6. Duplicate rows should not overwrite existing attendance records.
7. Name-only duplicate checking should not be trusted.
8. Event code should be used when possible to avoid importing responses into the wrong event.
9. All import actions must be logged.
10. Valid attendance records must always be linked to an event.

---

## 8. Recommended Optional Improvement

Add an `attendance_import_errors` table.

Suggested fields:

* id
* import_batch_id
* row_number
* error_type
* error_message
* raw_row_data
* created_at

Reason:

This makes import errors traceable and easier to review. It also prevents confusion when an admin asks why some rows failed.
