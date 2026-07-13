# Commenting Guidelines

Use Taglish comments that help Sofia understand and continue the codebase.
Comments should explain intent, business rules, and confusing flow. Keep code
names in English.

## Style

- Use short Taglish comments, usually 1-2 lines.
- Prefer simple words over formal technical wording.
- Explain why the code exists, not every small thing it does.
- Keep comments professional and easy to explain during defense.

## Comment When Useful

- File purpose: ano ang role ng file sa system.
- Function/class purpose: anong responsibility niya.
- Business rules: rules from the system requirements or supervisor.
- Non-obvious flow: multi-step logic na madaling malito.
- ORM relationships: clarify kung shortcut lang ba siya or real DB column.

## Avoid Noise

Huwag i-comment ang obvious syntax.

Bad:

```python
# Import FastAPI.
from fastapi import FastAPI

# Email ng user.
email = mapped_column(String(150), nullable=False)
```

Good:

```python
# Bawal maulit ang same email sa same event para maiwasan ang duplicate attendance.
UniqueConstraint("event_id", "email", name="uq_attendance_records_event_email")
```

## Tone

Use natural Taglish comments.

Good:

```python
# Isang DB session lang per request; automatic itong sinasara pagkatapos gamitin.
```

Avoid:

```python
# This persistence abstraction facilitates normalized geospatial reference compliance.
```

## Rule Of Thumb

Kapag obvious from the code, huwag lagyan ng comment. Kapag business decision,
system flow, or confusing relationship, lagyan ng short Taglish comment.
