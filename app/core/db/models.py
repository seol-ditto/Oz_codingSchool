import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, text, BigInteger, Integer
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from uuid6 import uuid7


class UUIDMixin:
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        CHAR(36), primary_key=True, default=uuid7
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), server_default=text("current_timestamp(0)")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.now(UTC), server_default=text("current_timestamp(0)")
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class Base(DeclarativeBase):
    """모든 모델이 상속하는 공통 Base"""
    pass


# SQLite는 기본키가 정확히 INTEGER일 때만 id를 자동 증가시킨다.
# 다른 DB(MySQL 등)에서는 BIGINT, SQLite에서는 INTEGER로 만들어지게 하는 타입
BigIntPK = BigInteger().with_variant(Integer, "sqlite")