"""Declarative base with deterministic constraint names.

Alembic needs stable names to alter or drop constraints later, so we set a
naming convention up front instead of letting Postgres invent them.
"""

from enum import StrEnum

from sqlalchemy import Enum, MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def enum_column(enum_cls: type[StrEnum], name: str) -> Enum:
    """Store a StrEnum as VARCHAR plus a CHECK constraint (not a native enum).

    Native Postgres enums are painful to change in migrations (adding a
    value needs ALTER TYPE, removing one is worse). VARCHAR + CHECK is
    just as safe and easy to evolve.
    """
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        length=32,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda e: [member.value for member in e],
    )
