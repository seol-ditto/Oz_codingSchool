# 토큰/비밀번호 관련 도구 모음

from datetime import datetime, timedelta, timezone

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


