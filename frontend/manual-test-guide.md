# Frontend Manual Test Guide

Gamitin ito pagkatapos naka-run ang backend at frontend servers.

## 1. Super Admin Setup

1. Mag-login bilang Super Admin sa `http://127.0.0.1:5500/`.
2. Sa `Organizational Units`, gumawa o i-check ang office/division na gagamitin.
3. Sa `Admin Users`, gumawa ng Program Admin account.
4. Sa `Programs`, gumawa ng program at i-assign ang Program Admin sa `Program Admins` action.
5. Gumawa ng event sa assigned program.
6. Sa event `Manage`, buksan ang `Fields`. I-set kung aling fields ang ipapakita at kung alin ang required.
7. I-hide ang isang configurable field, gaya ng `Signature`, at i-save.
8. Piliin ang `Generate QR/link`, pagkatapos subukan ang `Copy link` at `Download QR`.
9. Piliin ang `Open attendance`.

Expected: makikita ang QR code at public attendance link. Gumagana ang copied link at PNG download. Hindi lalabas sa public form ang hidden field. Hindi dapat mag-open ang attendance kung wala pang generated link/QR.

## 2. Public Attendee Flow

1. Buksan ang generated QR/link sa incognito o ibang browser profile.
2. Kumpletuhin ang required fields.
3. Kung gagamit ng address, piliin ang region, province kung applicable, city/municipality, at barangay nang sunod-sunod.
4. Piliin ang `Yes` o `No` sa documentation/publication consent.
5. I-check ang database-processing consent.
6. Mag-submit ng attendance.

Expected: pwedeng `No` ang documentation/publication consent. Mandatory ang database-processing consent dahil kailangan ito para ma-store at ma-process ang attendance record. Kapag parehong email ang sinubukang gamitin sa parehong event, dapat duplicate attendance error ang lalabas.

## 3. Program Admin Flow

1. Mag-login bilang assigned Program Admin.
2. I-check na assigned program at events lang ang nakikita.
3. Sa event, buksan ang `Attendance` at i-review ang submitted record.
4. Mag-update ng attendance status at maglagay ng reason.
5. I-close ang event pagkatapos ng collection period.
6. I-reopen ang closed event at i-check na tumatanggap ulit ito ng attendance.
7. I-close ulit ang event at gumawa ng PDF mula sa event o Reports page.

Expected: hindi makikita ng Program Admin ang `Organizational Units`, `Admin Users`, `PSGC Data`, at `Audit Logs`. Hindi rin siya dapat maka-access ng ibang program sa URL/API. Check marks ang gamit sa selected consent/sex values sa PDF.

## 4. Super Admin Verification

1. Sa `Organizational Units`, mag-deactivate ng unit na walang active child at i-restore ito.
2. Sa `PSGC Data`, gumawa o mag-update ng test PSGC record gamit ang official numeric code at tamang parent.
3. Sa `Reports`, piliin ang program at date range.
4. Buksan ang event summary at i-check ang attendance totals.
5. Sa `Audit Logs`, i-filter ang `event`, `attendance_record`, `attendance_sheet_export`, o PSGC actions.
6. I-archive lang ang event kapag closed na ito.

Expected: inactive unit ay hindi na available sa bagong assignment pero nananatili ang history nito. Ang PDF ay para sa selected event at valid attendees nito lamang.
