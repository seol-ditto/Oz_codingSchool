# API에 붙이는 인증/권한 확인 함수 모음(토큰 해석은 app/core/security.py 사용)
from typing import Annotated
# 종류 + 붙일 Depends를 한 덩어리로 묶어 이름을 붙이는 도구
from fastapi import Depends, HTTPException
# Depends: 다른 함수를 먼저 실행해 결과를 받아오는 도구
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
# HTTPBearer: 헤더에서 Bearer 토큰을 꺼내는 도구
# HTTPAuthorizationCredentials: 꺼낸 토큰을 담는 상자
from sqlalchemy.ext.asyncio import AsyncSession
# AsyncSession: 비동기 DB 세션의 종류 표시용
import jwt     # 토큰 에러 종류를 알아보기 위해

from app.core.db.databases import async_get_db   # DB 세션을 만들어주는 함수
from app.core.security import decode_access_token    # 토큰 해석 함수
from app.models.enums import Role, Department   # 권한 값(pending, staff, admin)
from app.models.users import User   # users 테이블 모델


bearer_scheme = HTTPBearer(auto_error=False)
# Authorization 헤더에서 토큰을 꺼내는 도구 생성
# auto_error=False : 헤더가 없으면 HTTPBearer가 마음대로 에러를 내버리는 것 방지 -> "헤더 없음"도 직접 401 에러 처리 가능
# schema: 구조, 설계도
# scheme: 방식

DBSession = Annotated[AsyncSession, Depends(async_get_db)]


# 토큰으로 로그인한 유저를 찾아주는 함수
# 실행 순서 예시
# 1. 누군가 API 호출 -> 헤더에 `Authorization: Bearer abc123`이 들어있음
# 2. FastAPI가 `get_current_user`를 실행하기 전에 `bearer_scheme`를 먼저 실행
# 3. `bearer_scheme`이 헤더를 읽어서 상자에 담음 -> 상자 안에는 `scheme(=Bearer)`과 `credentials(=abc123)`가 들어있음
# 4. 그 상자가 `credentials` 변수에 들어간 채로 함수 시작
async def get_current_user(
        db: DBSession,    # DB에서 유저를 조회할 세션
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),   # 헤더에서 꺼낸 토큰 상자(토큰은 credentials.credentials)
        # credentials = 변수 이름. 함수 안에서 이 이름으로 꺼내 씀
        # : HTTPAuthorizationCredentials = 이 변수에 들어올 종류 표시. "토큰 상자가 들어온다"라는 뜻
        # = Depends(bearer_scheme) = 이 변수에 무엇을 넣을지, "bearer_scheme를 먼저 실행하고, 그 결과를 credentials라는 변수에 넣어라"
) -> User:    # -> 뜻: 안내문(회원 한 명을 돌려줍니다.)
    # 헤더 확인: Authorization 헤더가 아예 없으면 401
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="인증 정보가 유효하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # try 안에서 해석해보고, 실패하면 except로 와서 401
    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, KeyError):   # InvalidTokenError: 만료/위조/형식 오류를 전부 포함하는 에러 이름
        raise HTTPException(                    # KeyError: 토큰 안에 user_id가 없는 경우
            status_code=401,
            detail="인증 정보가 유효하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # DB 조회: user_id로 유저 한 명 꺼내기(비동기라서 await 붙임)
    user = await db.get(User, user_id)
    # 유저 확인: 없는 유저면 401 비활성 유저면 403
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="인증 정보가 유효하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="비활성화된 계정입니다."
        )

    # 통과: 유저를 돌려줌
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# admin만 통과시키는 함수
async def get_current_admin(
        user: CurrentUser,   # 로그인 확인을 먼저 하고, 찾은 유저를 받아옴
) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다."
        )
    return user    # 통과한 유저를 API 함수에 넘겨줌


# staff, admin만 통과시키는 함수
async def get_current_staff(
        user: CurrentUser,
) -> User:
    if user.role not in (Role.ADMIN, Role.STAFF):    # 새 권한이 추가돼도 staff, admin만 통과시키도록
        raise HTTPException(
            status_code=403,
            detail="접근 권한이 없습니다."
        )
    return user    # 통과한 유저를 API 함수에 넘겨줌


StaffUser = Annotated[User, Depends(get_current_staff)]
AdminUser = Annotated[User, Depends(get_current_admin)]


# 의료진 staff 또는 admin만 통과시키는 함수 -> 환자 정보 등록, 진료기록 등록이 사용
async def get_current_medical_staff(
        user: StaffUser,
) -> User:
    if user.role == Role.ADMIN:
        return user

    if user.department != Department.MEDICAL:
        raise HTTPException(
            status_code=403,
            detail="의료진만 등록할 수 있습니다."
        )
    return user

MedicalStaffUser = Annotated[User, Depends(get_current_medical_staff)]