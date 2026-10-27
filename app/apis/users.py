from fastapi import APIRouter


router = APIRouter(prefix="/api/v1/users", tags=["users"])


# ======= [지희] 회원 정보 수정 / 비밀번호 변경 ======
# PATCH /me : 회원 정보 수정
# PATCH /me/password : 비밀번호 변경



# ======= [지수] 마이페이지 조회 / 회원 탈퇴 ======
# GET /me : 마이페이지 조회
# DELETE /me : 회원 탈퇴