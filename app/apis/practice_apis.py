import re       # 정규표현식 도구
import string   # 특수문자 모음 불러오기 위해

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field
# APIRouter : API 묶음을 만드는 도구
# Body : 요청 본문(Request body)에서 값을 받겠다고 명시할 때 사용
# HTTPException: 404 등 에러 응답을 보낼 때 사용
# Field: Path(...)가 경로변수에 조건을 건 것과 마찬가지로 모델 속성에 조건 부여

# 라우터 생성하기
# prefix: 이 라우터에 속한 모든 경로 앞에 자동으로 붙여줄 공통 주소(노션 endpoint)
router = APIRouter(prefix="/practice_api")

user_list = [
	{
		"id": 1,
		"name": "홍길동",
		"age": 24,
		"email": "gildong24@example.com",
		"password": "Password1234!!"
	},
	{
		"id": 2,
		"name": "장문복",
		"age": 21,
		"email": "moonluck12@example.com",
		"password": "Check1321!"
	},
	{
		"id": 3,
		"name": "임우진",
		"age": 31,
		"email": "limousine33@example.com",
		"password": "lwsPAssword12@"
	}
]

# 이메일 정규표현식: (아이디)@(도메인).(최상위 도메인 2글자 이상)
# alex@example.com
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
# 정규표현식 설명 추가
# [] 대괄호: 이 중 한 글자
	# 예시)[abc]는 a, b, c 중 아무거나 한 글자
# [a-z]는 a부터 z까지 중 한 글자
# [a-z]+는 a부터 z까지 한 글자 이상
# {2,} 중괄호: 앞의 것이 2개 이상
	# {2, 4}는 2개부터 4개까지
    # {3}은 정확히 3개
# ^: 문자열의 시작
# $: 문자열의 끝
# 위의 두 문자가 없으면 아무 곳에나 이메일 모양이 섞여있기만 해도 통과할 수 있음
	# 예시) 안녕gildong@test.com하세요 -> 통과
# 맨 앞의 r"...": 역슬래시를 글자 그대로 두세요요 -> 이걸 안 붙이면 .을 정규식 안에 표현할 수 없음



# 비밀번호 규칙 검사 (등록/수정에 모두 필요해서 따로 함수로 분리)
def check_password(password: str) -> str:
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=422,	# 422: Unprocessable Content: 형식은 맞는데 값이 규칙을 어김
            detail="비밀번호에 대문자가 1개 이상 포함되어야 합니다."
		)
    # string.punctuation: 특수문자 모음
    has_special = False
    for char in password:
        if char in string.punctuation:
            has_special = True

    if not has_special:
            raise HTTPException(
            status_code=422,
            detail="비밀번호에 특수문자가 1개 이상 포함되어야 합니다."
		)


# --------------------------------------------
# Pydantic 모델
# --------------------------------------------

# 응답 형식 : password를 빼서 클라이언트에 전달되지 않도록
class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: str

# 회원 등록 요청 형식: 모든 항목 필수(...)
class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=10) # 이름은 2글자 이상, 최대 10글자
    age: int = Field(..., ge=14)    # 14세 이상만 가입 가능
    email: str = Field(..., max_length=30, pattern=EMAIL_REGEX)
    password: str = Field(..., min_length=8, max_length=20)

# 회원 수정 요청 형식: 모든 항목 선택(기본값으로 None) -> 한 가지만 수정하고 싶을 수 있으니까
class UpdateUserRequest(BaseModel):
    age: int | None = Field(None, ge=14)
    email: str | None = Field(None, max_length=30, pattern=EMAIL_REGEX)
    password: str | None = Field(None, min_length=8, max_length=20)


# --------------------------------------------
# API
# --------------------------------------------

# 3. 회원 등록
@router.post(
    "/users",
    summary="회원 등록 API",
    response_model=UserResponse,
    status_code=201,	# 201: Created 생성에 성공했다
)
def create_user_handler(body: CreateUserRequest):
    # 비밀번호 조건 검사 -> 안 맞으면 422 에러 발생
    check_password(body.password)

	# 이메일 중복 검사
    for user in user_list:
        if user["email"] == body.email:
            raise HTTPException(
                status_code=409,	# 409: Conflict: 이미 존재하는 데이터와 충돌
                detail="이미 등록된 이메일입니다."
			)

	# id 자동 증가: 현재 가장 큰 id + 1
    new_id = 1
    for user in user_list:
        if user["id"] >= new_id:
            new_id = user["id"] + 1

    new_user = {
        "id": new_id,
        "name": body.name,
        "age": body.age,
        "email": body.email,
        "password": body.password,
	}
    user_list.append(new_user)
    return new_user    # 잘 등록됐는지 확인차

# 4. 회원 정보 수정
@router.patch(
    "/users/{user_id}",    # 모든 정보를 수정하면 put, 일부만 수정하면 patch
    summary="회원 정보 수정 API",
    response_model=UserResponse,
)
def update_user_handler(
    user_id: int,
    body: UpdateUserRequest = Body(...),
):
    # 아무 항목도 입력 안하면 400 Bad Request 응답 반환
    if body.age is None and body.email is None and body.password is None:
        raise HTTPException(
            status_code=400,
            detail="Bad Request: 수정할 항목을 입력하세요"
		)

	# 비밀번호를 입력했을 때는 대문자, 특수문자 검사 필요
    if body.password is not None:
        check_password(body.password)

    for user in user_list:
        if user["id"] == user_id:
            if body.age is not None:
                user["age"] = body.age
            if body.email is not None:
                user["email"] = body.email
            if body.password is not None:
                user["password"] = body.password
            return user
	
    raise HTTPException(
        staus_code=404,
        detail="회원을 찾을 수 없습니다."
	)