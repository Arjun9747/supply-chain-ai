import enum

import sqlalchemy as sa
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base class with standard PostgreSQL naming conventions."""

    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)


def enum_column(
    enum_cls: type[enum.Enum],
    name: str | None = None,
    native_enum: bool = False,
) -> sa.Enum:
    """Returns a configured sa.Enum column type for mapped_column().

    Uses native_enum=False and create_constraint=False to allow SQLAlchemy 2.0
    to infer string length automatically without generating duplicate DDL constraints.
    """
    return sa.Enum(
        enum_cls,
        name=name,
        native_enum=native_enum,
        create_constraint=False,
        values_callable=lambda x: [e.value for e in x],
    )
