from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.databases import Base


class XrayImage(Base):
    __tablename__ = "xray_images"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    ) # BigInteger: ERD에서 bigint

    record_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("medical_records.id", ondelete="CASCADE"), nullable=False
    ) # ForeignKey: "medical_records" 테이블의 id 컬럼

    uploader_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    ) # ERD에는 bigint라고 적혀있었지만, ForeignKey로 참조하는 대상과 타입이 동일해야하기 때문에 코드에는 Integer로 작성

    image_url: Mapped[str] = mapped_column(
        String(2048), nullable=False
    )
    shooting_datetime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )