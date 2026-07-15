# Frontend Manual Test Guide

Gamitin ito pagkatapos naka-run ang backend at frontend servers.

## 1. Super Admin Setup

1. Mag-login bilang Super Admin sa `http://127.0.0.1:5500/`.
2. Sa `Organizational Units`, gumawa o i-check ang office/division na gagamitin.
3. Sa `Admin Users`, gumawa ng Program Admin account.
4. Sa `Programs`, gumawa ng program at i-assign ang Program Admin sa `Program Admins` action.
5. Gumawa ng event sa assigned program.
6. Sa event `Manage`, i-check ang `Fields` requirements bago buksan ang attendance.
7. Piliin ang `Generate QR/link`, pagkatapos `Open attendance`.

Expected: makikita ang QR code at public attendance link. Hindi dapat mag-open ang attendance kung wala pang generated link/QR.

## 2. Public Attendee Flow

1. Buksan ang generated QR/link sa incognito o ibang browser profile.
2. Kumpletuhin ang required fields.
3. Kung gagamit ng address, piliin ang region, province kung applicable, city/municipality, at barangay nang sunod-sunod.
4. I-check ang database-processing consent.
5. Mag-submit ng attendance.

Expected: makikita ang success state. Kapag parehong email ang sinubukang gamitin sa parehong event, dapat duplicate attendance error ang lalabas.

## 3. Program Admin Flow

1. Mag-login bilang assigned Program Admin.
2. I-check na assigned program at events lang ang nakikita.
3. Sa event, buksan ang `Attendance` at i-review ang submitted record.
4. Mag-update ng attendance status at maglagay ng reason.
5. I-close ang event pagkatapos ng collection period.
6. Gumawa ng PDF mula sa event o Reports page.

Expected: hindi makikita ng Program Admin ang `Organizational Units`, `Admin Users`, at `Audit Logs`. Hindi rin siya dapat maka-access ng ibang program sa URL/API.

## 4. Super Admin Verification

1. Sa `Reports`, piliin ang program at date range.
2. Buksan ang event summary at i-check ang attendance totals.
3. Sa `Audit Logs`, i-filter ang `event`, `attendance_record`, o `attendance_sheet_export` actions.
4. I-archive lang ang event kapag closed na ito.

Expected: ang PDF ay para sa selected event at valid attendees nito lamang.
