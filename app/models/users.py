from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.databases import Base
from app.models.enums import Department, Gender, Role


class User(Base):
    __tablename__ = "users"
    # 실제 DB에 만들어질 테이블 이름, ERD의 테이블 이름과 동일해야 함!!
    # 다른 테이블이 외래키로 이 테이블을 가리킬 때도 이 이름 사용하게 됨

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    # email, hashed_password, name, phone_number에는 NOT NULL 표시가 없어서 "| None" 추가했음

    email: Mapped[str | None] = mapped_column(
        String(255), unique=True,
    )

    hashed_password: Mapped[str | None] = mapped_column(
        String(255), comment="평문 저장 X -> 해쉬화 된 비밀번호 저장",
    )

    name: Mapped[str | None] = mapped_column(String(20))

    phone_number: Mapped[str | None] = mapped_column(
        String(20), unique=True, comment="유저 핸드폰 번호",
    )

    gender: Mapped[Gender] = mapped_column(
        Enum(Gender), nullable=False, comment="성별 선택",
    )
    # Mapped[str | None]처럼 None이 붙으면 SQLAlchemy가 알아서 nullable=True로 만들고, 안 붙어있으면 nullable=False로 만들지만
    # ERD와 쉽게 비교하기 위해 nullable 옵션을 코드에 작성함

    department: Mapped[Department] = mapped_column(
        Enum(Department), nullable=False, comment="부서 선택",
    )

    role: Mapped[Role] = mapped_column(
        Enum(Role), nullable=False, comment="부여된 역할 권한",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1"), comment="계정 활성화 여부",
    )
    # default=True : 값이 비워져있으면 SQLAlchemy가 True로 채워서 보냄(기본값 설정)
    # 이 규칙은 Python 코드 안에만 존재하기 때문에 마이그레이션해도 MySQL 테이블 설계에는 기본값이 기록되지 않음
    # 테이블 설계 자체에 DEFAULT 1을 기록하고 싶으면 server_default=text("1")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="유저 생성 일시",
    )
    # server_default: 값이 비워져있으면 기본값을 DB가 직접 넣게 하는 옵션 -> 마이그레이션하면 테이블 설계에 DEFAULT CURRENT_TIMESTAMP로 들어감
    # func.now() : SQLAlchemy가 DB 종류에 맞는 "현재 시각" 함수로 바꿔줌 -> MySQL에서는 CURRENT_TIMESTAMP(now())로 만들어짐
    # default=datetime.now()라고 쓰면 서버가 켜질 때 딱 한번만 시각이 계산돼서 모든 회원의 created_at이 동일하게 맞춰져버림

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True, comment="유저 정보 수정 일시",
    )
    # onupdate: 행을 수정할 때마다 시각을 자동으로 바꿔주는 옵션