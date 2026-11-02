from fastapi import APIRouter, Response

from app.apis.dependencies import CurrentUser
from app.core.security import delete_refresh_cookie
from app.schemas.users import MessageResponse


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])



# ======= [시윤] 회원가입 / 로그인 / 토큰 재발급 ======
import jwt
from fastapi import APIRouter, Cookie, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.apis.dependencies import DBSession
from app.core.security import (
    REFRESH_COOKIE_NAME,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    set_refresh_cookie,
    verify_password,
)
from app.models.enums import Role
from app.models.users import User
from app.schemas.users import LoginRequest, SignupRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# POST /signup : 회원가입
@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(data: SignupRequest, db: DBSession):
    # 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다.")

    # 휴대폰 번호 중복 확인
    result = await db.execute(select(User).where(User.phone_number == data.phone_number))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="이미 사용 중인 휴대폰 번호입니다.")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        name=data.name,
        department=data.department,
        gender=data.gender,
        phone_number=data.phone_number,
        role=Role.PENDING,   # 가입 직후 대기자
        is_active=True,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        # 위 확인 직후 동시에 같은 값으로 가입한 드문 경우 대비 (unique 제약 위반)
        await db.rollback()
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다.")
    await db.refresh(user)
    return user


# POST /login : 로그인
# 로그인 -> POST /api/v1/auth/login
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, db: DBSession):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # 이메일 없음 / 비밀번호 불일치는 같은 메시지 (hashed_password가 비어 있는 회원도 실패 처리)
    if (
        user is None
        or user.hashed_password is None
        or not verify_password(data.password, user.hashed_password)
    ):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")

    # 리프레시 토큰은 쿠키로, 액세스 토큰은 본문으로
    set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenResponse(access_token=create_access_token(user.id))


# POST / refresh : 토큰 재발급
@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    db: DBSession,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="리프레시 토큰이 없습니다. 다시 로그인해주세요.")

    try:
        user_id = decode_refresh_token(refresh_token)
    except jwt.ExpiredSignatureError:  # 만료를 먼저 잡아야 함
        raise HTTPException(status_code=401, detail="리프레시 토큰이 만료되었습니다. 다시 로그인해주세요.")
    except (jwt.InvalidTokenError, KeyError):
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다. 다시 로그인해주세요.")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다. 다시 로그인해주세요.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")

    return TokenResponse(access_token=create_access_token(user.id))



# ======= [지희] 로그아웃 ======
# POST /logout : 로그아웃
@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response, _user: CurrentUser):
    # 브라우저에 저장된 리프레시 토큰 쿠키 삭제
    delete_refresh_cookie(response)

    # 로그아웃 성공 응답
    return MessageResponse(message="로그아웃되었습니다.")