# API가 주고받는 데이터의 모양을 정하는 파일

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import Department, Gender, Role


# ===== 공통 =====
# (UserResponse, MessageResponse)

# 회원 전체 정보 응답 -> 회원가입 등에서 사용
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # DB에서 꺼낸 User 객체를 이 모양으로 바로 바꿀 수 있게 하는 설정

    id: int
    email: str | None
    name: str | None
    department: Department
    gender: Gender
    phone_number: str | None
    role: Role
    is_active: bool
    # hashed_password는 없어야 함


# 안내 문구만 돌려주는 공통 응답 -> 로그아웃, 비밀번호 변경, 회원 탈퇴 등이 사용
class MessageResponse(BaseModel):
    message: str



# ===== [시윤] 회원가입 / 로그인 / 토큰 재발급 =====
# 회원가입 요청 -> POST /api/v1/auth/signup
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    department: Department
    gender: Gender
    phone_number: str

# 로그인 요청 -> POST /api/v1/auth/login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# 토큰 응답 -> POST /api/v1/auth/login, POST /api/v1/auth/refresh
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    


# ===== [지희] 회원 정보 수정 / 비밀번호 변경 / 로그아웃 =====





# ===== [지수] 마이페이지 조회 / 회원 탈퇴 =====





# ===== [설아] 회원 목록 조회 / 회원 권한 변경 =====
# 회원 목록 조회 응답 (회원 1명 분 내용) -> GET /api/v1/admin/users
class UserListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None
    name: str | None
    department: Department
    gender: Gender
    phone_number: str | None
    is_active: bool


# 권한 변경 요청 -> PATCH /api/v1/admin/users/{user_id}/role
class RoleUpdateRequest(BaseModel):
    role: Role


# 권한 변경 응답 -> PATCH /api/v1/admin/users/{user_id}/role
class RoleUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None
    name: str | None
    role: Role