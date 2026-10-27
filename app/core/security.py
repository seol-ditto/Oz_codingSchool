# 토큰/비밀번호 관련 도구 모음
from datetime import datetime, timedelta, timezone

from fastapi import Response
import jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()
# 추천 방식(Argon2)으로 해시하는 도구를 만들라는 뜻



# -------------------------------------------------------
# 비밀번호 관련 함수
# -------------------------------------------------------

# 비밀번호를 해시로 바꾸기 -> 회원가입/비밀번호 변경 API가 사용
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# 입력한 비밀번호가 맞는지 확인 -> 로그인/비밀번호 변경 API가 사용
def verify_password(
        password: str,
        hashed_password: str
) -> bool:
    return password_hash.verify(password, hashed_password)



# -------------------------------------------------------
# 토큰 관련 함수
# -------------------------------------------------------

# 액세스 토큰 만들기(SECRET_KEY, 30분) -> 로그인/재발급 API가 사용
def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# 리프레시 토큰 만들기(REFRESH_SECRET_KEY, 7일) -> 로그인 API가 사용
def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(payload, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)


# 액세스 토큰 해석해서 user_id 꺼내기 -> app/apis/dependencies.py의 get_current_user 함수가 사용
def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload["user_id"]


# 리프레시 토큰 해석 -> 재발급 API가 사용
def decode_refresh_token(token: str) -> int:
    payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload["user_id"]



# -------------------------------------------------------
# 리프레시 토큰 쿠키 설정: 심기(로그인), 지우기(로그아웃)가 같은 이름과 Path를 써야 쿠키가 지워짐
# -------------------------------------------------------
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


# 리프레시 토큰을 쿠키에 심기 -> 로그인 API가 사용
def set_refresh_cookie(
        response: Response,
        refresh_token: str
) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        # 쿠키 수명(초) -> 7일 * 24시간 * 60분 * 60초
        path=REFRESH_COOKIE_PATH,
        # 이 주소 아래 API에만 쿠키를 보냄
        httponly=True,
        # 자바스크립트가 읽지 못하도록(요구사항의 http_only)
        samesite="lax",
        # 다른 사이트에서 몰래 보내는 요청에는 쿠키를 안 붙이겠다
        secure=False,
        # 로컬은 http라서 False -> 나중에 배포하게 된다면 True로 변경 필요!!
    )


# 리프레시 토큰 쿠키 지우기 -> 로그아웃 API가 사용
def delete_refresh_cookie(
        response: Response,
) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH
    )