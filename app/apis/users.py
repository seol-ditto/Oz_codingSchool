from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.apis.dependencies import CurrentUser, DBSession
from app.models.users import User
from app.schemas.users import (
    UserResponse,
    UserUpdateRequest,
    PasswordUpdateRequest,
    MessageResponse,
)
from app.core.security import hash_password, verify_password


router = APIRouter(prefix="/api/v1/users", tags=["users"])

# ===== [지희] 회원 정보 수정 =====

@router.patch("/me", response_model=UserResponse)
async def update_my_info(
    data: UserUpdateRequest,
    user: CurrentUser,
    db: DBSession,
):
    # 요청에 포함된 필드만 가져오기
    update_data = data.model_dump(exclude_unset=True)

    # 휴대폰 번호 중복 확인
    if "phone_number" in update_data and update_data["phone_number"] is not None:
        result = await db.execute(
            select(User).where(
                User.phone_number == update_data["phone_number"],
                User.id != user.id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="이미 사용 중인 휴대폰 번호입니다.",
            )

    # 실제로 전달된 필드만 수정
    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="이미 사용 중인 휴대폰 번호입니다.",
        )

    return user


# ===== [지희] 비밀번호 변경 =====
@router.patch("/me/password", response_model=MessageResponse)
async def update_my_password(
    data: PasswordUpdateRequest,
    user: CurrentUser,
    db: DBSession,
):
    # 1. 현재 비밀번호 확인
    if not user.hashed_password or not verify_password(
        data.current_password, user.hashed_password
    ):
        raise HTTPException(
            status_code=400,
            detail="현재 비밀번호가 일치하지 않습니다.",
        )

    # 2. 새 비밀번호를 해시로 변환
    user.hashed_password = hash_password(data.new_password)

    # 3. DB에 저장
    await db.commit()

    # 4. 성공 응답
    return MessageResponse(message="비밀번호가 성공적으로 변경되었습니다.")

# ======= [지수] 마이페이지 조회 / 회원 탈퇴 ======
# GET /me : 마이페이지 조회
# DELETE /me : 회원 탈퇴
