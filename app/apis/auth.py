from fastapi import APIRouter


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ======= [시윤] 회원가입 / 로그인 / 토큰 재발급 ======
# POST /signup : 회원가입
# POST /login : 로그인
# POST / refresh : 토큰 재발급



# ======= [지희] 로그아웃 ======
# POST /logout : 로그아웃