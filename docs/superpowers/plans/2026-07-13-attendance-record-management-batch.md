# Attendance Record Management Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver role-aware attendance record listing, details, protected signatures, audited status updates, and consistent project documentation.

**Architecture:** A dedicated attendance-record router, schema module, and service own the admin-facing record workflow. A reusable audit-row builder keeps audit creation inside the caller's transaction, while the existing signature service safely resolves private files. Existing MySQL tables remain unchanged.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic, MySQL 8, Pillow, Pytest, Mermaid, Draw.io.

## Global Constraints

- Super Admin can access all attendance records.
- Program Admin can access and update status only under actively assigned programs.
- No attendee-field editing and no hard deletion.
- Signature storage paths never appear in JSON.
- Status and audit writes use one transaction.
- No MySQL schema or ERD structure change.
- Follow `docs/commenting-guidelines.md` with concise Taglish comments.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Paginated Event Attendance List

**Files:**
- Create: `backend/tests/test_attendance_record_routes.py`
- Create: `backend/app/schemas/attendance_records.py`
- Create: `backend/app/services/attendance_record_service.py`
- Create: `backend/app/api/attendance_records.py`
- Modify: `backend/app/api/router.py`

**Interfaces:**
- Produces: `AttendanceRecordPage`, `list_event_attendance_records`, and `GET /api/events/{event_id}/attendance-records`.
- Consumes: `get_current_user`, `Event`, `AttendanceRecord`, and `ProgramAdminAssignment`.

- [x] **Step 1: Add failing list-route tests**

Cover the response shape, default pagination, status/search query construction,
stable newest-first ordering, Super Admin access, active assignment access,
revoked/unassigned denial, missing event, validation bounds, and authentication.

```python
def test_list_event_attendance_returns_paginated_summary():
    response = client.get("/api/events/5/attendance-records")
    assert response.status_code == 200
    assert response.json()["data"]["pagination"] == {
        "page": 1,
        "page_size": 25,
        "total_items": 1,
        "total_pages": 1,
    }


def test_assigned_program_admin_can_list_event_attendance():
    response = client.get("/api/events/5/attendance-records")
    assert response.status_code == 200
    assert "program_admin_assignments" in session.checked_statements
```

- [x] **Step 2: Run the list tests and verify RED**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_attendance_record_routes.py -q
```

Expected: route tests fail with `404` because the attendance-record router does
not exist.

- [x] **Step 3: Implement list contracts and query service**

Use these core interfaces:

```python
AttendanceStatus = Literal["valid", "duplicate", "invalid", "void"]


@dataclass
class AttendanceRecordPage:
    items: list[AttendanceRecord]
    page: int
    page_size: int
    total_items: int
    total_pages: int


def list_event_attendance_records(
    db: Session,
    event_id: int,
    current_user: User,
    *,
    page: int,
    page_size: int,
    attendance_status: str | None,
    search: str | None,
) -> AttendanceRecordPage:
    event = db.get(Event, event_id)
    if event is None:
        raise AttendanceEventNotFoundError
    _ensure_program_access(db, event.program_id, current_user)

    filters = [AttendanceRecord.event_id == event_id]
    if attendance_status is not None:
        filters.append(AttendanceRecord.attendance_status == attendance_status)
    if search is not None:
        pattern = f"%{search.lower()}%"
        full_name = func.lower(
            func.concat_ws(
                " ",
                AttendanceRecord.first_name,
                AttendanceRecord.middle_name,
                AttendanceRecord.last_name,
                AttendanceRecord.suffix,
            )
        )
        filters.append(
            or_(
                full_name.like(pattern),
                func.lower(AttendanceRecord.email).like(pattern),
                func.lower(AttendanceRecord.affiliation).like(pattern),
                func.lower(AttendanceRecord.designation_category).like(pattern),
            )
        )

    total_items = db.scalar(
        select(func.count(AttendanceRecord.attendance_id)).where(*filters)
    ) or 0
    items = list(
        db.scalars(
            select(AttendanceRecord)
            .where(*filters)
            .order_by(
                AttendanceRecord.submitted_at.desc(),
                AttendanceRecord.attendance_id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return AttendanceRecordPage(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=ceil(total_items / page_size) if total_items else 0,
    )
```

The service must:

- Load the event and return `EventNotFoundError` when absent.
- Allow Super Admin immediately; otherwise require an active assignment for
  `event.program_id` and `current_user.user_id`.
- Filter by event ID and optional status.
- Search case-insensitively across name fields, email, affiliation, and
  designation/category.
- Run one count query and one paginated query.
- Order by `submitted_at DESC, attendance_id DESC`.

Register the router and return:

```python
success_response(
    {
        "items": [_attendance_summary(record) for record in result.items],
        "pagination": {
            "page": result.page,
            "page_size": result.page_size,
            "total_items": result.total_items,
            "total_pages": result.total_pages,
        },
    },
    "Attendance records retrieved.",
)
```

- [x] **Step 4: Run focused list tests until GREEN**

Run the Task 1 tests and confirm all list/auth/validation scenarios pass.

---

### Task 2: Attendance Detail And Protected Signature

**Files:**
- Modify: `backend/tests/test_attendance_record_routes.py`
- Modify: `backend/tests/test_signature_service.py`
- Modify: `backend/app/schemas/attendance_records.py`
- Modify: `backend/app/services/attendance_record_service.py`
- Modify: `backend/app/services/signature_service.py`
- Modify: `backend/app/api/attendance_records.py`

**Interfaces:**
- Produces: `get_attendance_record`, `resolve_signature_image`, detail route, and protected PNG route.
- Consumes: Task 1's record access check and the configured `SIGNATURE_DIRECTORY`.

- [x] **Step 1: Add failing detail and signature tests**

Cover full event/program/consent/address output, historical inactive PSGC names,
no private path leakage, assigned/unassigned access, image success, typed-only
404, missing file 404, traversal rejection, `private, no-store`, and auth.

```python
def test_attendance_detail_never_returns_private_signature_path():
    response = client.get("/api/attendance-records/20")
    assert response.status_code == 200
    assert "signature_image_path" not in response.text
    assert response.json()["data"]["signature"]["has_image"] is True


def test_protected_signature_returns_private_png():
    response = client.get("/api/attendance-records/20/signature")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "private, no-store"
```

- [x] **Step 2: Run new tests and verify RED**

Expected: detail and signature routes return `404`; resolver tests fail because
`resolve_signature_image` is missing.

- [x] **Step 3: Implement eager detail loading and safe file resolution**

Use these interfaces:

```python
def get_attendance_record(
    db: Session,
    attendance_id: int,
    current_user: User,
) -> AttendanceRecord:
    record = db.scalar(
        select(AttendanceRecord)
        .options(
            selectinload(AttendanceRecord.event).selectinload(Event.program),
            selectinload(AttendanceRecord.address).selectinload(
                AttendanceRecordAddress.region
            ),
            selectinload(AttendanceRecord.address).selectinload(
                AttendanceRecordAddress.province
            ),
            selectinload(AttendanceRecord.address).selectinload(
                AttendanceRecordAddress.city_municipality
            ),
            selectinload(AttendanceRecord.address).selectinload(
                AttendanceRecordAddress.barangay
            ),
        )
        .where(AttendanceRecord.attendance_id == attendance_id)
    )
    if record is None:
        raise AttendanceRecordNotFoundError
    _ensure_program_access(db, record.event.program_id, current_user)
    return record


def resolve_signature_image(
    directory: Path,
    relative_path: str | None,
) -> Path | None:
    if not relative_path:
        return None
    base_directory = directory.resolve()
    candidate = (base_directory / relative_path).resolve()
    try:
        candidate.relative_to(base_directory)
    except ValueError:
        return None
    if candidate.suffix.lower() != ".png" or not candidate.is_file():
        return None
    return candidate
```

The detail query eagerly loads event, program, optional address, and all PSGC
relationships without filtering inactive reference rows. The resolver must
resolve both base and candidate paths, require the candidate to remain under
the base directory, and return only an existing regular `.png` file.

The signature route uses `FileResponse` with:

```python
headers={"Cache-Control": "private, no-store"}
```

- [x] **Step 4: Run detail/signature and regression tests until GREEN**

Run attendance-record route tests plus `tests/test_signature_service.py`.

---

### Task 3: Role-Aware Status Update And Atomic Audit

**Files:**
- Modify: `backend/tests/test_attendance_record_routes.py`
- Create: `backend/tests/test_audit_service.py`
- Create: `backend/app/services/audit_service.py`
- Modify: `backend/app/schemas/attendance_records.py`
- Modify: `backend/app/services/attendance_record_service.py`
- Modify: `backend/app/api/attendance_records.py`

**Interfaces:**
- Produces: `build_audit_log`, `update_attendance_status`, and `PATCH /api/attendance-records/{attendance_id}/status`.
- Consumes: Task 1's access check and Task 2's detail response formatter.

- [x] **Step 1: Add failing status and audit tests**

Cover all four statuses, required trimmed reason, Super Admin, assigned Program
Admin, revoked assignment, idempotency, exact audit fields, one commit, rollback
on failure, and authentication.

```python
def test_assigned_program_admin_updates_status_with_audit():
    response = client.patch(
        "/api/attendance-records/20/status",
        json={"attendance_status": "void", "reason": "Wrong attendee email."},
    )
    assert response.status_code == 200
    assert attendance.attendance_status == "void"
    assert session.added_audit.action == "attendance_status_changed"
    assert session.added_audit.user_id == 2


def test_same_status_is_idempotent_without_audit():
    response = client.patch(
        "/api/attendance-records/20/status",
        json={"attendance_status": "valid", "reason": "Confirmed as valid."},
    )
    assert response.status_code == 200
    assert session.added_audit is None
```

- [x] **Step 2: Run status tests and verify RED**

Expected: status route returns `404` and audit helper import fails until the
production interfaces are added.

- [x] **Step 3: Implement audit builder and transactional status update**

Use these interfaces:

```python
def build_audit_log(
    *,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    description: str,
    old_values: dict[str, Any] | None,
    new_values: dict[str, Any] | None,
    ip_address: str | None,
    user_agent: str | None,
) -> AuditLog:
    return AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description[:500],
        old_values_json=old_values,
        new_values_json=new_values,
        ip_address=ip_address[:45] if ip_address else None,
        user_agent=user_agent[:500] if user_agent else None,
    )


def update_attendance_status(
    db: Session,
    attendance_id: int,
    payload: UpdateAttendanceStatusRequest,
    current_user: User,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> AttendanceRecord:
    attendance = get_attendance_record(db, attendance_id, current_user)
    old_status = attendance.attendance_status
    if old_status == payload.attendance_status:
        return attendance

    attendance.attendance_status = payload.attendance_status
    audit_log = build_audit_log(
        user_id=current_user.user_id,
        action="attendance_status_changed",
        entity_type="attendance_record",
        entity_id=attendance.attendance_id,
        description=(
            f"Attendance status changed from {old_status} to "
            f"{payload.attendance_status}. Reason: {payload.reason}"
        ),
        old_values={"attendance_status": old_status},
        new_values={
            "attendance_status": payload.attendance_status,
            "reason": payload.reason,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    try:
        db.commit()
    except Exception:
        db.rollback()
        attendance.attendance_status = old_status
        raise
    db.refresh(attendance)
    return attendance
```

For a real change, assign the new status, build and add one audit row, commit
once, and refresh the attendance record. On any write exception, rollback and
re-raise. Clamp IP/user-agent to their schema lengths. Do not alter
`duplicate_flag`.

- [x] **Step 4: Run Task 3 and all attendance tests until GREEN**

Run attendance record, audit service, public attendance, and signature tests.

---

### Task 4: Documentation, DFD, And Final Verification

**Files:**
- Create: `others/README.md`
- Modify: `backend/README.md`
- Modify: `others/backend/backend-api-plan.md`
- Modify: `others/backend/fastapi-stack-decision.md`
- Modify: `others/database/README.md`
- Modify: `others/mvp-requirements-v1.md`
- Modify: `others/system-process-flow.md`
- Modify: `others/user-roles-and-permission-matrix.md`
- Modify: `others/handoff.txt`
- Modify: `others/dict-attendance-system-handoff.md`
- Modify: `others/dfd/level-1/dfd-level-1-text.md`
- Modify: `others/dfd/level-2/dfd-level-2-text.md`
- Modify: `others/dfd/source/dfd-level-1.mmd`
- Modify: `others/dfd/source/dfd-level-2.mmd`
- Regenerate: current Level 1/2 PNG, SVG, and Draw.io artifacts
- Modify: this implementation plan's checkboxes

**Interfaces:**
- Consumes: all verified endpoint and permission behavior from Tasks 1-3.
- Produces: one consistent documentation hierarchy and editable/current DFD artifacts.

- [x] **Step 1: Update authoritative documentation**

Document the four endpoints, pagination, assigned Program Admin status
permission, required reason, protected signatures, and transactional audit.
Remove the tentative attendee-correction endpoint from the current MVP plan.

- [x] **Step 2: Mark historical files and resolve stale decisions**

Create `others/README.md` with the source-of-truth hierarchy. Add a clear
historical/non-authoritative notice to handoff and scratch-era guidance. Resolve
JWT, signature storage, signature requirement, PSGC collection, and local
database-name examples in current docs.

- [x] **Step 3: Update and regenerate DFD artifacts**

Level 1 must show Super Admin/Program Admin attendance review flowing through
assignment checks, D5 Attendance Records, and D7 Audit Logs. Level 2 must add
the detailed status-review process. Update text and Mermaid first, then
regenerate PNG/SVG and editable Draw.io files with the existing render scripts.

- [x] **Step 4: Run final verification**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app scripts
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m scripts.orm_smoke_check
```

Also verify:

- OpenAPI contains all four attendance-record routes.
- The detail schema contains no `signature_image_path`.
- The signature response is protected and private.
- `git diff --check` passes.
- Documentation conflict scans no longer report resolved decisions as open.
- Regenerated Level 1/2 PNG, SVG, Mermaid, and Draw.io artifacts are present
  and visually consistent.

- [x] **Step 5: Review the scoped diff**

Confirm there are no ERD/schema changes, unrelated refactors, generated cache
files, or user-owned changes outside the approved batch.
