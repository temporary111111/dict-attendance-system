import importlib


def test_build_audit_log_maps_values_and_clamps_request_metadata():
    audit_service = importlib.import_module("app.services.audit_service")

    audit = audit_service.build_audit_log(
        user_id=2,
        action="attendance_status_changed",
        entity_type="attendance_record",
        entity_id=20,
        description="Attendance status changed.",
        old_values={"attendance_status": "valid"},
        new_values={"attendance_status": "void", "reason": "Invalid."},
        ip_address="1" * 50,
        user_agent="a" * 550,
    )

    assert audit.user_id == 2
    assert audit.action == "attendance_status_changed"
    assert audit.entity_type == "attendance_record"
    assert audit.entity_id == 20
    assert audit.description == "Attendance status changed."
    assert audit.old_values_json == {"attendance_status": "valid"}
    assert audit.new_values_json == {
        "attendance_status": "void",
        "reason": "Invalid.",
    }
    assert audit.ip_address == "1" * 45
    assert audit.user_agent == "a" * 500
