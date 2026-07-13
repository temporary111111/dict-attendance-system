"""Shared SQLAlchemy base ng lahat ng ORM models.

Kapag nag-inherit ang class sa Base, nagiging part siya ng model metadata.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
