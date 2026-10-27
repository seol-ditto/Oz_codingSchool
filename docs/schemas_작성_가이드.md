# `app/schemas/users.py` 작성 가이드

User API의 요청/응답 모양(스키마)을 한 파일에 같이 작성하기 위한 규칙입니다.
PR 리뷰 때는 맨 아래 **리뷰 체크리스트**로 확인합니다.

---

## 1. 파일 구조

```python
# ===== 공통 =====
# UserResponse, MessageResponse

# ===== [시윤] 회원가입 / 로그인 / 토큰 재발급 =====

# ===== [지희] 회원 정보 수정 / 비밀번호 변경 / 로그아웃 =====

# ===== [지수] 마이페이지 조회 / 회원 탈퇴 =====

# ===== [설아] 회원 목록 조회 / 회원 권한 변경 =====
```

- 자기 구역 **헤더 바로 아래**에만 작성하기
- 다른 사람 구역의 헤더, 코드, 빈 줄은 건드리지 않기
- 구역 사이 빈 줄(2~3줄)은 지우지 않기 → Git 충돌 방지용
- 공통 구역(`UserResponse`, `MessageResponse`)을 바꿔야 하면 수정 전에 카톡으로 먼저 공유하기

---

## 2. 이름 규칙

| 종류 | 규칙 | 예시 |
| --- | --- | --- |
| 요청 | 기능 + `Request` | `SignupRequest`, `LoginRequest`, `PasswordUpdateRequest`, `RoleUpdateRequest` |
| 응답 | 기능 + `Response` | `TokenResponse`, `MyPageResponse`, `UserListItemResponse` |

- 클래스 이름은 대문자로 시작 (`RoleUpdateRequest`)
- 필드 이름은 공통 사항 규칙대로 소문자 + 밑줄 (`phone_number`, `is_active`)

---

## 3. 작성 규칙

1. **필드는 내 명세서 표와 똑같이**
   - 이름, 종류, 필수 여부를 명세서 "본문 필드" / "성공 응답" 표 그대로 옮기기
   - 요구사항에 없는 필드를 추가하거나, 있는 필드를 빼지 않기

2. **필수 여부 쓰는 법**
   - 필수 Y → `email: str`
   - 필수 N → `department: Department | None = None`

3. **권한·부서·성별은 `str` 대신 enum 사용**
   - `role: Role`, `department: Department`, `gender: Gender`
   - 정해진 값이 아니면 FastAPI가 자동으로 422를 보내줌

4. **DB에서 꺼낸 User를 그대로 넘기는 응답에는 설정 추가**
   ```python
   model_config = ConfigDict(from_attributes=True)
   ```

5. **응답에 `hashed_password` 절대 넣지 않기**

6. **User 모델에서 비어 있을 수 있는 필드는 응답에서도 `| None`**
   - `email`, `name`, `phone_number` → `str | None`

7. **공통 스키마로 충분하면 새로 만들지 않기**
   - 회원 정보 8개 전체 응답 → `UserResponse`
   - 안내 문구만 응답 → `MessageResponse`

8. **클래스 위에 주석 한 줄**
   - 어떤 API의 요청/응답인지: `# 회원 권한 변경 요청 -> PATCH /api/v1/admin/users/{user_id}/role`

9. **새 import가 필요하면**
   - 맨 위 import 줄은 모두가 같이 쓰는 곳이라 충돌이 나기 쉬움
   - 추가했다면 PR 본문에 적어두기, 충돌 나면 "Accept Both Changes"

---

## 4. 예시 (설아 구역)

```python
# 회원 목록 조회 응답 (회원 한 명분) -> GET /api/v1/admin/users
class UserListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None
    name: str | None
    department: Department
    gender: Gender
    phone_number: str | None
    is_active: bool


# 회원 권한 변경 요청 -> PATCH /api/v1/admin/users/{user_id}/role
class RoleUpdateRequest(BaseModel):
    role: Role
```

- 목록 응답은 스키마에 리스트를 만들지 않고, 라우터에서 `list[UserListItemResponse]`로 사용
- 권한 변경 응답(`id, email, name, role`)도 명세서 필드에 맞춰 따로 만들기

### 참고: 부분 수정(PATCH) 요청

회원 정보 수정처럼 "보낸 것만 바꾸는" 요청은 모든 필드를 필수 N으로 만들기

```python
# 회원 정보 수정 요청 -> PATCH /api/v1/users/me
class UserUpdateRequest(BaseModel):
    department: Department | None = None
    phone_number: str | None = None
```

라우터에서 `data.model_dump(exclude_unset=True)`로 꺼내면 실제로 보낸 필드만 나옴

---

## 5. 리뷰 체크리스트

PR 리뷰할 때 하나씩 확인하기

- [ ] 본인 구역에만 작성했는가 (다른 구역, 구역 사이 빈 줄 그대로인가)
- [ ] 이름이 `기능 + Request / Response` 규칙을 따르는가
- [ ] 필드가 본인 명세서 표와 정확히 같은가 (빠진 것, 추가된 것 없음)
- [ ] 필수 Y/N이 명세서와 같은가 (`| None = None` 여부)
- [ ] 권한·부서·성별에 enum을 썼는가
- [ ] 응답에 `hashed_password`가 없는가
- [ ] DB 객체를 넘기는 응답에 `from_attributes=True`가 있는가
- [ ] `UserResponse` / `MessageResponse`로 충분한데 중복으로 만들지 않았는가
- [ ] 클래스 위에 어떤 API용인지 주석이 있는가
- [ ] 새 import를 추가했다면 PR 본문에 적었는가
