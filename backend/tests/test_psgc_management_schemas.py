import pytest
from pydantic import ValidationError

from app.schemas.psgc_management import (
    PsgcCodeUpdateRequest,
    PsgcDeleteRequest,
    PsgcManagementQuery,
    PsgcNameUpdateRequest,
)


def test_code_update_accepts_a_ten_digit_numeric_replacement_code():
    request = PsgcCodeUpdateRequest(
        new_code="0500500000",
        reason="Verified against the PSA publication.",
        confirmed=True,
    )

    assert request.new_code == "0500500000"
    assert request.confirmed is True


@pytest.mark.parametrize("new_code", ["05005", "05005000001", "05005ABCDE"])
def test_code_update_rejects_an_invalid_replacement_code(new_code):
    with pytest.raises(ValidationError):
        PsgcCodeUpdateRequest(
            new_code=new_code,
            reason="Verified against the PSA publication.",
            confirmed=True,
        )


def test_name_update_requires_a_meaningful_audit_reason():
    with pytest.raises(ValidationError):
        PsgcNameUpdateRequest(name="Albay", reason="ok")


def test_delete_request_requires_an_explicit_confirmation():
    with pytest.raises(ValidationError):
        PsgcDeleteRequest(reason="Duplicate test record.", confirmed=False)


def test_management_query_rejects_an_unsupported_level_and_page_size():
    with pytest.raises(ValidationError):
        PsgcManagementQuery(level="district", page_size=101)
