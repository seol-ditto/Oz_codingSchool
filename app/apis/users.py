from fastapi import APIRouter, Response

from app.apis.dependencies import CurrentUser, DBSession
from app.core.security import delete_refresh_cookie
from app.schemas.users import MyPageResponse, MessageResponse
router = APIRouter(prefix="/api/v1/users", tags=["users"])


# ======= [지희] 회원 정보 수정 / 비밀번호 변경 ======
# PATCH /me : 회원 정보 수정
# PATCH /me/password : 비밀번호 변경



# ======= [지수] 마이페이지 조회 / 회원 탈퇴 ======
# GET /me : 마이페이지 조회
@router.get("/me", response_model=MyPageResponse)
async def get_my_page(user: CurrentUser):
    return user

# DELETE /me : 회원 탈퇴
@router.delete("/me", response_model=MessageResponse)
async def delete_my_account(
    user: CurrentUser,
    db: DBSession,
    response: Response,
):
    await db.delete(user)
    await db.commit()

    delete_refresh_cookie(response)

    return MessageResponse(message="회원 탈퇴가 완료되었습니다.")