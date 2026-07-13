"""Reusable audit row builder na hindi kusang nagko-commit ng transaction."""

from typing import Any

from app.models import AuditLog


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
    """Bumubuo lang ng row para maisama sa transaction ng main action."""
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
