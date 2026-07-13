# Public Attendance Batch Design

## Goal

Deliver the public event page data, fixed attendance submission, PSGC dropdown
lookups, duplicate prevention, and private signature handling as one batch.

## Public Endpoints

- `GET /api/public/events/{eventCode}`
- `POST /api/public/events/{eventCode}/attendance`
- `GET /api/psgc/regions`
- `GET /api/psgc/provinces?regionCode=...`
- `GET /api/psgc/cities-municipalities?regionCode=...&provinceCode=...`
- `GET /api/psgc/barangays?cityMunicipalityCode=...`

These endpoints require no admin token. Public event lookup excludes archived
events and returns whether attendance is currently accepted without exposing
admin account data.

## Submission Contract

Attendance uses `multipart/form-data` so fixed text fields and one optional
signature image can be submitted together. Required attendee fields are first
name, last name, affiliation, designation/category, sex, email, both consent
choices, and either typed signature text or an image. Middle name and suffix
are optional. Database-processing consent must be true because the submission
cannot be stored legally or operationally without it; documentation/publication
consent may be false.

The event must exist and have `open` status. Email is normalized to lowercase
and is unique per event. A duplicate returns `409 DUPLICATE_ATTENDANCE` without
creating another row or signature file.

## Address and PSGC Rules

The whole address section is optional. If any address value is supplied,
`region_code`, `city_municipality_code`, and `barangay_code` are required.
`province_code` remains optional because some PSGC cities are not
province-based. Every selected PSGC row must be active and its parent codes
must match the submitted hierarchy. Free-text fields map to `street_address`
and `postal_code` in the current normalized schema.

PSGC lookup routes return active rows only. PSA/PSGC data remains locally stored;
submission never depends on a live PSA API.

## Signature Privacy

Uploaded signatures accept PNG or JPEG up to a configurable byte limit. Pillow
verifies the image and re-encodes it as PNG to strip metadata. Files are stored
under private `SIGNATURE_DIRECTORY`; unlike QR codes, this directory is not
mounted as a public static route. The database stores only a relative path for
later authorized report generation.

## Architecture

- `schemas/public_attendance.py` defines public responses and form validation.
- `services/public_attendance_service.py` owns event, duplicate, PSGC, and write rules.
- `services/signature_service.py` owns private image verification and storage.
- `services/psgc_service.py` owns active dropdown queries.
- `api/public_attendance.py` and `api/psgc.py` expose focused public routes.
- The attendance and optional address are committed in one database transaction.

## Testing

Tests cover public event states, all PSGC filters, successful text/image
signatures, consent, incomplete and mismatched addresses, closed events,
duplicates, upload validation, cleanup on database conflicts, authentication
independence, full regression, MySQL ORM smoke check, and OpenAPI registration.
