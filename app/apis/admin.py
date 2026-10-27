from fastapi import APIRouter, HTTPException
from sqlalchemy import or_, select

from app.apis.dependencies import AdminUser, DBSession
from app.models.enums import Department
from app.models.users import User
from app.schemas.users import UserListItemResponse, RoleUpdateRequest, RoleUpdateResponse


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ====== 회원 목록 조회: GET /users =======
@router.get(                                        # GET 방식
    "/users",
    summary="회원 목록 조회 API",
    response_model=list[UserListItemResponse]   # 응답은 UserListItemResponse 목록 모양으로 내보내라 -> 스키마에 없는 필드는 응답에서 빠짐
)
async def get_users(
    _: AdminUser,   # 어드민 유저인지만 확인하고 코드 내부에서 부를 일이 없어서 _로 설정
    db: DBSession,
    search: str | None = None,
    department: Department | None = None,
):
    query = select(User).order_by(User.id)  # 모든 회원을 조회 가능하고, 검색 기능 활용 가능(이름, 이메일)

    if search:
        query = query.where(
            or_(User.email.contains(search), User.name.contains(search))
        )
    if department:
        query = query.where(User.department == department)

    result = await db.execute(query)    # 비동기라서 await
    return result.scalars().all()


# ====== 회원 권한 변경 PATCH /users/{user_id}/role =======
@router.patch(                          # 일부 변경이니까 PATCH
    "/users/{user_id}/role",
    summary="회원 권한 변경 API",
    response_model=RoleUpdateResponse,
)
async def update_user_role(
    user_id: int,                       # 주소 안의 {user_id}와 매개변수 user_id: int의 이름이 같아서 FastAPI가 알아서 숫자를 꺼내옴
    data: RoleUpdateRequest,            # 스키마 종류로 받으면 FastAPI가 요청 본문에서 읽음. 잘못된 role이면 명세서의 422 에러가 나감
    admin: AdminUser,
    db: DBSession,
):
    if admin.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="본인의 권한은 변경할 수 없습니다."
        )
    
    user = await db.get(User, user_id)  # id로 회원 한 명 꺼내기
    if user is None:                    # 없는 회원이면 404 에러
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 회원입니다."
        )

    user.role = data.role               # 꺼낸 회원의 권한 변경하기(아직 DB에는 저장 x)
    await db.commit()                   # DB에 저장
    await db.refresh(user)              # 저장된 최신 값으로 다시 읽기
    return user                         # 새로고침된 값 반환(response_model로 RoleUpdateResponse를 설정해둬서 id, email, name, role만 응답)