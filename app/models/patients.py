from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.databases import Basee  # 팀 공용 Base 
from app.models.enums import Gender  # 팀 공용 enums에서 import




class Patient(Base):
    __tablename__ = "patients"

    # SQLite는 BIGINT PK에 autoincrement가 안 먹어서 sqlite에서만 INTEGER로 처리
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String(30), nullable=False, comment="환자 성명")
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="환자 나이")
    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, name="gender"), nullable=True, comment="환자 성별"
    )
    phone: Mapped[str] = mapped_column(
        String(11), nullable=False, comment="환자 연락처, 국내 전화번호로 한정"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="환자 정보 등록 일시"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, onupdate=func.now(), comment="환자 정보 수정 일시"
    )