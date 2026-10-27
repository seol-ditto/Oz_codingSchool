from fastapi import APIRouter, Response

from app.apis.dependencies import CurrentUser
from app.core.security import delete_refresh_cookie
from app.schemas.users import MessageResponse


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ===== [지희] 로그아웃 =====
@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response, _user: CurrentUser):
    # 브라우저에 저장된 리프레시 토큰 쿠키 삭제
    delete_refresh_cookie(response)

    # 로그아웃 성공 응답
    return MessageResponse(message="로그아웃되었습니다.")
# ======= [시윤] 회원가입 / 로그인 / 토큰 재발급 ======
# POST /signup : 회원가입
# POST /login : 로그인
# POST / refresh : 토큰 재발급



# ======= [지희] 로그아웃 ======
# POST /logout : 로그아웃
