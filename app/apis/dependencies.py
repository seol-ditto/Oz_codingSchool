# API에 붙이는 인증/권한 확인 함수 모음(토큰 해석은 security.py 완성 후 연결)

from fastapi import Depends, HTTPException
# Depends: 다른 함수를 먼저 실행해 결과를 받아오는 도구
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
# HTTPBearer: 헤더에서 Bearer 토큰을 꺼내는 도구
# HTTPAuthorizationCredentials: 꺼낸 토큰을 담는 상자
from sqlalchemy.ext.asyncio import AsyncSession
# AsyncSession: 비동기 DB 세션의 종류 표시용

from app.core.db.databases import async_get_db   # DB 세션을 만들어주는 함수
from app.models.enums import Role   # 권한 값(pending, staff, admin)
from app.models.users import User   # users 테이블 모델


bearer_scheme = HTTPBearer()
# Authorization 헤더에서 토큰을 꺼내는 도구 생성
# schema: 구조, 설계도
# scheme: 방식


# 토큰으로 로그인한 유저를 찾아주는 함수
# 실행 순서 예시
# 1. 누군가 API 호출 -> 헤더에 `Authorization: Bearer abc123`이 들어있음
# 2. FastAPI가 `get_current_user`를 실행하기 전에 `bearer_scheme`를 먼저 실행
# 3. `bearer_scheme`이 헤더를 읽어서 상자에 담음 -> 상자 안에는 `scheme(=Bearer)`과 `credentials(=abc123)`가 들어있음
# 4. 그 상자가 `credentials` 변수에 들어간 채로 함수 시작
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),   # 헤더에서 꺼낸 토큰 상자(토큰은 credentials.credentials)
        # credentials = 변수 이름. 함수 안에서 이 이름으로 꺼내 씀
        # : HTTPAuthorizationCredentials = 이 변수에 들어올 종류 표시. "토큰 상자가 들어온다"라는 뜻
        # = Depends(bearer_scheme) = 이 변수에 무엇을 넣을지, "bearer_scheme를 먼저 실행하고, 그 결과를 credentials라는 변수에 넣어라"
        db: AsyncSession = Depends(async_get_db),   # DB에서 유저를 조회할 세션
) -> User:    # -> 뜻: 안내문(회원 한 명을 돌려줍니다.)
    # TODO 1: 토큰 해석
    # TODO 2: 토큰에서 user_id 꺼내기(키 이름 확정 후)
    # TODO 3: user = await db.get(User, user_id)
    # TODO 4: user가 없거나 is_active가 False면 401
    pass


# admin만 통과시키는 함수
async def get_current_admin(
        user: User = Depends(get_current_user),   # 로그인 확인을 먼저 하고, 찾은 유저를 받아옴
) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다."
        )
    return user    # 통과한 유저를 API 함수에 넘겨줌


# staff, admin만 통과시키는 함수
async def get_current_staff(
        user: User = Depends(get_current_user),
) -> User:
    if user.role not in (Role.ADMIN, Role.STAFF):    # 나중에 권한이 3개 이상으로 늘어나도 staff, admin만 통과시키도록
        raise HTTPException(
            status_code=403,
            detail="접근 권한이 없습니다."
        )
    return user    # 통과한 유저를 API 함수에 넘겨줌