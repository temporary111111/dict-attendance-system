from types import SimpleNamespace

import pytest

from app.models import AuditLog, PSGCRegion
from app.services.psgc_management_service import (
    PsgcCodeAlreadyExistsError,
    PsgcRecordInUseError,
    delete_record,
    update_code,
    update_name,
)


class MutationSession:
    """Maliit na in-memory session para sa PSGC write-rule tests."""

    def __init__(self, records, dependency_counts=(0, 0)):
        self.records = records
        self.dependency_counts = iter(dependency_counts)
        self.added = []
        self.deleted = []
        self.committed = False
        self.rolled_back = False

    def get(self, model, key):
        return self.records.get((model, key))

    def scalar(self, statement):
        return next(self.dependency_counts)

    def add(self, record):
        self.added.append(record)

    def delete(self, record):
        self.deleted.append(record)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, record):
        return None


def test_update_name_saves_old_and_new_values_with_the_admin_reason():
    region = PSGCRegion(region_code="0500000000", region_name="Old Region V")
    session = MutationSession({(PSGCRegion, region.region_code): region})

    updated = update_name(
        session,
        level="region",
        code=region.region_code,
        name="Region V (Bicol Region)",
        reason="Verified against the PSA publication.",
        user_id=7,
    )

    assert updated is region
    assert region.region_name == "Region V (Bicol Region)"
    audit = next(record for record in session.added if isinstance(record, AuditLog))
    assert audit.old_values_json == {"name": "Old Region V"}
    assert audit.new_values_json == {"name": "Region V (Bicol Region)"}
    assert "Verified against the PSA publication." in audit.description
    assert session.committed is True


def test_code_update_is_blocked_when_the_record_has_child_locations():
    region = PSGCRegion(region_code="0500000000", region_name="Region V")
    session = MutationSession(
        {(PSGCRegion, region.region_code): region}, dependency_counts=(2, 0)
    )

    with pytest.raises(PsgcRecordInUseError) as error:
        update_code(
            session,
            level="region",
            code=region.region_code,
            new_code="0500100000",
            reason="Verified correction.",
            user_id=7,
        )

    assert error.value.child_count == 2
    assert error.value.attendance_address_reference_count == 0
    assert region.region_code == "0500000000"
    assert session.committed is False


def test_code_update_rejects_an_existing_code_before_mutating_the_record():
    source = PSGCRegion(region_code="0500000000", region_name="Region V")
    existing = PSGCRegion(region_code="0500100000", region_name="Existing region")
    session = MutationSession(
        {
            (PSGCRegion, source.region_code): source,
            (PSGCRegion, existing.region_code): existing,
        }
    )

    with pytest.raises(PsgcCodeAlreadyExistsError):
        update_code(
            session,
            level="region",
            code=source.region_code,
            new_code=existing.region_code,
            reason="Verified correction.",
            user_id=7,
        )

    assert source.region_code == "0500000000"
    assert session.committed is False


def test_delete_removes_only_a_dependency_free_record_and_writes_an_audit_log():
    region = PSGCRegion(region_code="0500000000", region_name="Temporary test region")
    session = MutationSession(
        {(PSGCRegion, region.region_code): region}, dependency_counts=(0, 0)
    )

    delete_record(
        session,
        level="region",
        code=region.region_code,
        reason="Removing a dependency-free test record.",
        user_id=7,
    )

    assert session.deleted == [region]
    assert any(isinstance(record, AuditLog) for record in session.added)
    assert session.committed is True
