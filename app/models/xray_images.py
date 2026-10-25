from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.databases import Base


class XrayImage(Base):
    __tablename__ = "xray_images"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    # BigInteger: ERD에서 bigint

    record_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("medical_records.id", ondelete="CASCADE"),
        nullable=False, comment="진료 기록 id",
    )
    # ForeignKey: "medical_records" 테이블의 id 컬럼

    uploader_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True, comment="X-ray 이미지를 업로드한 유저의 id",
    )
    # ERD에는 bigint라고 적혀있었지만, ForeignKey로 참조하는 대상과 타입이 동일해야하기 때문에 코드에는 Integer로 작성
    # ERD의 not null과 delete: set null은 동시에 적용할 수 없어서 삭제 규칙을 우선해 nullable로 변경

    image_url: Mapped[str] = mapped_column(
        String(2048), nullable=False, comment="이미지 url",
    )

    shooting_datetime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="X-ray 촬영일시",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="X-ray 이미지 등록 일시",
    )