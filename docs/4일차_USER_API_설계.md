# 4일차_USER API 설계
## 목차
- [공통 사항 정리](#공통-사항-정리)
- [1. 회원가입 REQ-USER-001](#1-회원가입-req-user-001)
- [2. 로그인 REQ-USER-002](#2-로그인-req-user-002)
- [3. 토큰 재발급 NFR-USER-001](#3-토큰-재발급-nfr-user-001)
- [4. 로그아웃 REQ-USER-003](#4-로그아웃-req-user-003)
- [5. 회원 탈퇴 REQ-USER-009](#5-회원-탈퇴-req-user-009)
- [6. 마이페이지 조회 REQ-USER-006](#6-마이페이지-조회-req-user-006)
- [7. 회원 정보 수정 REQ-USER-007](#7-회원-정보-수정-req-user-007)
- [8. 비밀번호 변경 REQ-USER-008](#8-비밀번호-변경-req-user-008)
- [9. 회원 목록 조회 REQ-USER-004](#9-회원-목록-조회-req-user-004)
- [10. 회원 권한 변경 REQ-USER-005](#10-회원-권한-변경-req-user-005)

## 요구사항 정의서란?
- 사용자 요구사항 정의서(User Requirements Document, URD)
- IT 프로젝트에서 사용자 및 이해관계자가 시스템을 통해 달성하고자 하는 목표, 기능, 제약 사항 등을 구체적으로 기술한 문서
- 개발할 소프트웨어가 무엇을 해야 하는지를 명확히 해서 프로젝트의 방향성을 제시
- 기획/디자인/개발/테스터 간 원활한 소통을 돕는 필수적인 기준

## API 명세서란?
- API Specification
- 애플리케이션 프로그래밍 인터페이스(API)의 기능, 동작 구조, 사용법 등을 명확하고 상세하게 정리한 기술 문서
- 프론트엔드와 백엔드 개발자 간 협업의 기반
- HTTP 메소드, 엔드포인트(url), 요청/응답 형식, 파라미터 등 API 호출에 필요한 모든 정보 포함

--- 

# 4조_USER API 명세서
## 공통 사항 정리
### 작성 규칙
- 해당 없는 칸(예: 쿼리 파라미터, 응답 Headers)은 지우지 말고, 설명에 "없음"으로 적기
- 실패 응답이 여러 개면 실패 블록을 복사해서 추가하기
### 엔드포인트(url) 규칙
- 가입/로그인/토큰/로그아웃: `/api/v1/auth/...`
- 본인 관련: `/api/v1/users/me`
- 어드민: `/api/v1/admin/users`
### 필드 이름
- 영어 소문자와 밑줄로 통일
- email, password, name, department, gender, phone_number, role, is_active

### 권한/부서 값 표기
- 권한: 
    - 대기: pending
    - 스태프: staff
    - 어드민: admin
- 부서
    - 연구: research
    - 의료: medical
    - 개발: develop
### 에러 형식
- 에러 메시지는 `{"detail": "메시지"}` 모양으로 한 줄로 적기
- 인증이 필요한 API는 비활성 회원이면 403 `{"detail": "비활성화된 계정입니다."}`
- 단, 422(필수값 누락/형식 오류)는 FastAPI가 자동으로 보내는 에러이기 때문에 예시 명세서의 422 모양을 그대로 복사하기

### NFR-USER-002 비밀번호 입력 보안
- 비밀번호 입력 시 마스킹 처리, 보기 아이콘 클릭할 때만 확인 가능(화면 처리, 별도 API 없음)
### NFR-USER-003 API 성능
- 모든 유저 API는 최대 3초 이내에 로직 처리하고 응답한다.


## 1. 회원가입 (REQ-USER-001)
- 담당: 홍시윤
- 요구사항
    ```text
    사내 의료인, 개발 실무진은 회원가입을 통해 흉부 X-Ray AI 진단 서비스를 이용할 수 있어야한다.

    회원가입 시 요구되는 항목은 다음과 같다.
        • 이메일
        • 비밀번호
        • 이름
        • 부서(연구, 의료, 개발)
        • 성별(M / F)
        • 휴대폰 번호
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원가입 |
| 설명 | 이메일, 비밀번호, 이름, 부서, 성별, 휴대폰 번호를 입력받아 신규 회원을 생성한다. 가입 직후 권한은 pending(대기자), 계정 활성화 여부는 true로 설정된다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/signup` |
| 메서드(Method) | POST |
| 인증 필요 여부 | N (비로그인 상태에서 호출) |


### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 본문 형식 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| email | string | Y | 이메일 형식, 중복 불가. 로그인 ID로 사용 |
| password | string | Y | 비밀번호. 서버에서 해시하여 저장하며 응답에 포함하지 않음 |
| name | string | Y | 이름 |
| department | string | Y | 부서. research(연구) / medical(의료) / develop(개발) 중 하나 |
| gender | string | Y | 성별. M / F 중 하나 |
| phone_number | string | Y | 휴대폰 번호 (예: 010-1234-5678) |


#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

### 3) 응답 (Response)
#### 성공
- 201 Created
```JSON
{
  "id": 1,
  "email": "oz@example.com",
  "name": "김오즈",
  "department": "medical",
  "gender": "F",
  "phone_number": "010-1234-5678",
  "role": "pending",
  "is_active": true
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 회원 고유 ID |
| email | string | 이메일 |
| name | string | 이름 |
| department | string | 부서 (research / medical / develop) |
| gender | string | 성별 (M / F) |
| phone_number | string | 휴대폰 번호 |
| role | string | 권한. 가입 시 기본값 pending |
| is_active | boolean | 계정 활성화 여부. 가입 시 true |


#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 본문 형식 |

#### 실패
- 409 Conflict (이메일 중복)
```JSON
{"detail": "이미 사용 중인 이메일입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

<br>

- 409 Conflict (휴대폰 번호 중복)
```JSON
{"detail": "이미 사용 중인 휴대폰 번호입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

<br>

- 422 Unprocessable Entity (필수값 누락 / 형식 오류, FastAPI 자동 응답)
```JSON
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | array | 검증 오류 목록 |
| detail[].type | string | 오류 종류 (예: missing, value_error) |
| detail[].loc | array | 오류가 발생한 위치 (예: ["body", "email"]) |
| detail[].msg | string | 오류 메시지 |
| detail[].input | any | 입력된 값 |

### 4) 비고
- 비밀번호는 평문으로 저장하지 않고 해시하여 저장한다.
- 가입 직후 권한은 pending이며, admin이 권한을 변경하기 전에는 마이페이지 외 서비스에 접근할 수 없다.


## 2. 로그인 (REQ-USER-002)
- 담당: 홍시윤
- 요구사항
    ```text
    회원가입을 한 사내 개발진, 의료 실무진, 연구진은 이메일과 비밀번호를 입력하여 로그인을 진행한 후 서비스를 이용할 수 있다.
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 로그인 |
| 설명 | 이메일과 비밀번호를 검증한 뒤 JWT를 발급한다. 액세스 토큰은 응답 본문으로, 리프레시 토큰은 http_only 쿠키로 전달한다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/login` |
| 메서드(Method) | POST |
| 인증 필요 여부 | N |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 본문 형식 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| email | string | Y | 가입한 이메일 |
| password | string | Y | 비밀번호 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

### 3) 응답 (Response)
#### 성공
- 200 OK 
```JSON
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| access_token | string | 액세스 토큰(JWT). 만료 30분. 페이로드에는 user_id만 포함 |
| token_type | string | 토큰 종류. 항상 bearer |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 본문 형식 |
| Set-Cookie | refresh_token=eyJhbGciOi...; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=604800 | 리프레시 토큰(JWT). 만료 7일. 클라이언트 JS에서 접근 불가 |

#### 실패
- 401 Unauthorized (이메일 없음 또는 비밀번호 불일치)
```JSON
{"detail": "이메일 또는 비밀번호가 올바르지 않습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

<br>

- 403 Forbidden (비활성화된 계정)
```JSON
{"detail": "비활성화된 계정입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

<br>

- 422 Unprocessable Entity (필수값 누락 / 형식 오류, FastAPI 자동 응답)
```JSON
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "password"],
      "msg": "Field required",
      "input": {"email": "hong@example.com"}
    }
  ]
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | array | 검증 오류 목록 |
| detail[].type | string | 오류 종류 |
| detail[].loc | array | 오류가 발생한 위치 |
| detail[].msg | string | 오류 메시지 |
| detail[].input | any | 입력된 값 |



### 4) 비고
- 이메일 없음과 비밀번호 불일치는 계정 존재 여부 노출을 막기 위해 같은 메시지로 응답한다.
- 토큰 페이로드에는 최소 식별 정보인 user_id만 저장한다. (만료 시각 exp 등 표준 클레임 제외) 권한(role)은 토큰에 넣지 않고 API 호출 시 DB에서 확인한다.
- 액세스 토큰은 이후 API 요청의 Authorization: Bearer {access_token} 헤더로 전달한다.
- pending(대기자) 권한도 로그인은 가능하며, 마이페이지 외 서비스 접근은 각 API의 인가 단계에서 막는다.
- 리프레시 토큰 쿠키 이름은 refresh_token, Path는 /api/v1/auth로 통일한다. (로그아웃에서 쿠키를 삭제할 때 동일한 값 사용)


## 3. 토큰 재발급 (NFR-USER-001)
- 담당: 홍시윤
- 요구사항
    ```text
    로그인 시 JWT(Json Web Token)을 발급하며, 이를 API 인가에 사용한다.

    엑세스 토큰의 만료주기는 30분, 리프레시 토큰의 만료주기는 7일로 한다.

    엑세스 토큰 만료 시 리프레시 토큰을 통해 엑세스 토큰을 재발급 할 수 있으며 리프레시 토큰도 만료되면 재로그인을 유도한다.

    리프레시 토큰은 클라이언트에서 접근할 수 없도록 http_only 쿠키로 전달한다.

    JWT 토큰의 페이로드에는 최소식별 정보인 user_id만 저장한다.
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 액세스 토큰 재발급 |
| 설명 | 쿠키로 전달된 리프레시 토큰을 검증하여 새로운 액세스 토큰을 발급한다. 리프레시 토큰이 만료되었거나 유효하지 않으면 401을 반환하고, 클라이언트는 로그인 페이지로 이동시킨다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/refresh` |
| 메서드(Method) | POST |
| 인증 필요 여부 | N (액세스 토큰은 불필요, refresh_token 쿠키 필요) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Cookie | `refresh_token={refresh_token}` | 로그인 시 발급된 리프레시 토큰. 브라우저가 자동 전송 (클라이언트 요청 시 credentials: "include" 설정 필요) |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

### 3) 응답 (Response)
#### 성공
- 200 OK 
```JSON
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| access_token | string | 새로 발급된 액세스 토큰(JWT). 만료 30분. 페이로드에는 user_id만 포함 |
| token_type | string | 토큰 종류. 항상 bearer |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 본문 형식 |

#### 실패
- 401 Unauthorized (리프레시 토큰 쿠키 없음)
```JSON
{"detail": "리프레시 토큰이 없습니다. 다시 로그인해주세요."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

<br>

- 401 Unauthorized (리프레시 토큰 만료)
```JSON
{"detail": "리프레시 토큰이 만료되었습니다. 다시 로그인해주세요."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

<br>

- 401 Unauthorized (유효하지 않은 리프레시 토큰)
```JSON
{"detail": "유효하지 않은 리프레시 토큰입니다. 다시 로그인해주세요."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |


### 4) 비고
- 액세스 토큰 만료 주기는 30분, 리프레시 토큰 만료 주기는 7일이다.
- 클라이언트는 API 호출이 토큰 만료로 401을 받으면 이 API를 호출해 새 액세스 토큰으로 재시도한다. 이 API도 401이면 재로그인을 유도한다.
- 리프레시 토큰은 HttpOnly 쿠키로만 전달되어 JS에서 접근할 수 없다. 이 API는 새 리프레시 토큰을 발급하지 않으므로 Set-Cookie는 응답하지 않는다.
- 토큰 페이로드에는 user_id만 저장하며, 존재하지 않거나 비활성화된 user_id의 토큰은 유효하지 않은 토큰으로 처리한다.


## 4. 로그아웃 (REQ-USER-003)
- 담당: 이지희
- 요구사항
    ```text
    로그인 유저는 상시 헤더에 노출되는 로그아웃 버튼을 통해 로그아웃을 진행할 수 있으며, 로그아웃 시 로그인 페이지로 전환된다.
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 로그아웃 |
| 설명 | 로그인한 사용자의 리프레시 토큰 쿠키를 만료 처리하여 로그아웃한다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/logout` |
| 메서드(Method) | POST |
| 인증 필요 여부 | Y (로그인 필요) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인 사용자 인증을 위한 JWT 액세스 토큰 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 요청 본문 없음 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 사용하지 않음 |

### 3) 응답 (Response)
#### 성공
- 200 OK

```json
{"message": "로그아웃되었습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| message | string | 로그아웃 성공 메시지 |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 데이터가 JSON 형식임을 나타냄 |
| Set-Cookie | refresh_token=; Max-Age=0; Path=/api/v1/auth; HttpOnly; Secure; SameSite=Lax | 리프레시 토큰 쿠키 만료 처리 |

#### 실패

- 401 Unauthorized (로그인 인증 실패)

```json
{"detail": "인증 정보가 유효하지 않습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 인증 실패 사유 |



### 4) 비고
- 로그인한 사용자는 상단 헤더의 로그아웃 버튼을 통해 로그아웃할 수 있다.
- 로그아웃 성공 시 프론트엔드에서 보관 중인 액세스 토큰을 삭제하고 로그인 페이지로 이동한다.
- 서버는 로그아웃 응답에서 리프레시 토큰 쿠키를 만료 처리한다.
- 리프레시 토큰 쿠키 삭제 시 로그인 API와 동일한 쿠키 이름(refresh_token)과 경로(Path=/api/v1/auth)를 사용한다.


## 5. 회원 탈퇴 (REQ-USER-009)
- 담당: 김지수
- 요구사항
    ```text
    모든 로그인 유저는 마이페이지에서 회원탈퇴 버튼을 통해 회원탈퇴를 진행할 수 있다.

    회원탈퇴 시 Database에서 회원과 관련된 정보는 모두 즉시 삭제한다.
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 탈퇴 |
| 설명 | 로그인한 사용자가 탈퇴를 요청하면 회원과 관련된 정보를 즉시 삭제한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | DELETE |
| 인증 필요 여부 | Y (로그인 필요) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 사용자의 액세스 토큰 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 요청 본문 없음 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

### 3) 응답 (Response)
#### 성공
- 200 OK

```JSON
{"message": "회원 탈퇴가 완료되었습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| message | string | 회원 탈퇴 완료 메시지 |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 본문 형식 |
| Set-Cookie | refresh_token=; Max-Age=0; Path=/api/v1/auth; HttpOnly; Secure; SameSite=Lax | 리프레시 토큰 쿠키 만료 처리 |

#### 실패
- 401 Unauthorized (토큰이 없거나 유효하지 않은 경우)

```JSON
{"detail": "인증 정보가 유효하지 않습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 인증 실패 메시지 |

### 4) 비고
- 로그인한 사용자만 회원 탈퇴를 요청할 수 있다.
- 회원 탈퇴 시 해당 회원과 관련된 정보를 데이터베이스에서 즉시 삭제한다.
- 탈퇴한 계정으로는 더 이상 로그인할 수 없다.


## 6. 마이페이지 조회 (REQ-USER-006)
- 담당: 김지수
- 요구사항
    ```text
    모든 로그인 유저는 마이페이지에서 본인의 정보를 확인할 수 있다.

    조회 가능한 항목
        • 이름
        • 이메일
        • 부서(연구, 의료, 개발)
        • 성별(M / F)
        • 휴대폰 번호
        • 권한(대기자, 스태프, 어드민)
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 마이페이지 조회 |
| 설명 | 로그인한 사용자가 자신의 이름, 이메일, 부서, 성별, 휴대폰 번호, 권한을 조회한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | GET |
| 인증 필요 여부 | Y (로그인 필요) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 사용자의 액세스 토큰 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 요청 본문 없음 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

### 3) 응답 (Response)
#### 성공
- 200 OK

```JSON
{
  "name": "김오즈",
  "email": "oz@example.com",
  "department": "medical",
  "gender": "F",
  "phone_number": "010-1234-5678",
  "role": "pending"
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| name | string | 회원 이름 |
| email | string | 회원 이메일 |
| department | string | 부서 (research / medical / develop) |
| gender | string | 성별 (M / F) |
| phone_number | string | 휴대폰 번호 |
| role | string | 권한 (pending / staff / admin) |


#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 본문 형식 |


#### 실패
- 401 Unauthorized (토큰이 없거나 유효하지 않은 경우)

```JSON
{"detail": "인증 정보가 유효하지 않습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 인증 실패 메시지 |


### 4) 비고
- 로그인한 사용자만 마이페이지를 조회할 수 있다.
- 로그인한 사용자 본인의 정보만 조회할 수 있다.
- 비밀번호 등 민감한 정보는 응답에 포함하지 않는다.


## 7. 회원 정보 수정 (REQ-USER-007)
- 담당: 이지희
- 요구사항
    ```text
    모든 로그인 유저는 마이페이지에서 본인의 정보를 수정할 수 있다.

    회원 정보 수정은 Partial로 이루어진다.

    수정가능한 항목
        • 부서
        • 휴대폰번호
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 정보 수정 |
| 설명 | 로그인한 사용자가 본인의 부서 및 휴대폰 번호를 부분 수정한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | PATCH |
| 인증 필요 여부 | Y (로그인 필요) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인 사용자 인증을 위한 JWT 액세스 토큰 |
| Content-Type | application/json | 요청 본문이 JSON 형식임을 나타냄 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| department | string | N | 변경할 부서 (research, medical, develop) |
| phone_number | string | N | 변경할 휴대폰 번호 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 사용하지 않음 |

### 3) 응답 (Response)
#### 성공
- 200 OK 

```json
{
  "name": "김오즈",
  "email": "oz@example.com",
  "department": "medical",
  "gender": "F",
  "phone_number": "010-1234-5678",
  "role": "staff"
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| name | string | 회원 이름 |
| email | string | 회원 이메일 |
| department | string | 회원 부서 (research / medical / develop) |
| gender | string | 회원 성별 (M / F) |
| phone_number | string | 회원 휴대폰 번호 |
| role | string | 회원 권한 (pending / staff / admin) |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 데이터가 JSON 형식임을 나타냄 |

#### 실패
- 401 Unauthorized

```json
{"detail": "인증 정보가 유효하지 않습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 인증 실패 사유 |


- 409 Conflict (휴대폰 번호 중복)
```JSON
{"detail": "이미 사용 중인 휴대폰 번호입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |


- 422 Unprocessable Entity (부서 값이 research, medical, develop이 아닌 경우)
```json
{
    "detail": [
        {
            "type": "enum",
            "loc": ["body", "department"],
            "msg": "Input should be 'research', 'medical' or 'develop'",
            "input": "sales"
        }
    ]
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | array | 검증 오류 목록 |
| detail[].type | string | 오류 종류 |
| detail[].loc | array | 오류가 발생한 위치 |
| detail[].msg | string | 오류 메시지 |
| detail[].input | any | 입력된 값 |

### 4) 비고
- department와 phone_number만 부분 수정할 수 있다.
- 요청에 포함되지 않은 필드는 기존 값을 유지한다.
- 수정할 필드 없이 빈 JSON 객체({})를 전송한 경우, 기존 회원 정보를 변경하지 않고 200 OK 응답을 반환한다.


## 8. 비밀번호 변경 (REQ-USER-008)
- 담당: 이지희
- 요구사항
    ```text
    모든 로그인 유저는 마이페이지에서 계정의 비밀번호를 변경할 수 있다.

    유저가 입력한 기존 비밀번호가 일치하는 지 검증한 후 새로운 비밀번호를 적용한다.

    입력항목
        • 기존 비밀번호
        • 새로운 비밀번호
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 비밀번호 변경 |
| 설명 | 로그인한 사용자가 현재 비밀번호를 확인한 후 새 비밀번호로 변경한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me/password` |
| 메서드(Method) | PATCH |
| 인증 필요 여부 | Y (로그인 필요) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인 사용자 인증을 위한 JWT 액세스 토큰 |
| Content-Type | application/json | 요청 본문이 JSON 형식임을 나타냄 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| current_password | string | Y | 현재 사용 중인 비밀번호 |
| new_password | string | Y | 변경할 새로운 비밀번호 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 사용하지 않음 |

### 3) 응답 (Response)
#### 성공
- 200 OK 

```json
{"message": "비밀번호가 성공적으로 변경되었습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| message | string | 비밀번호 변경 성공 메시지 |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 데이터가 JSON 형식임을 나타냄 |

#### 실패
- 400 Bad Request (현재 비밀번호 불일치)

```json
{"detail": "현재 비밀번호가 일치하지 않습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 비밀번호 확인 실패 사유 |


- 401 Unauthorized (로그인 인증 실패)

```json
{"detail": "인증 정보가 유효하지 않습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 인증 실패 사유 |


- 422 Unprocessable Entity (요청 데이터 검증 실패)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "new_password"],
      "msg": "Field required"
    }
  ]
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | array | 검증 오류 목록 |
| detail[].type | string | 오류 종류 |
| detail[].loc | array | 오류가 발생한 위치 |
| detail[].msg | string | 오류 메시지 |

### 4) 비고
- 현재 비밀번호가 일치하는 경우에만 새 비밀번호로 변경한다.
- 비밀번호는 응답 데이터에 포함하지 않는다.
- 비밀번호 관련 입력값이 오류 응답에 노출되지 않도록 처리한다.
- 보안상 422 응답에서 input(입력값) 필드는 제외한다.


## 9. 회원 목록 조회 (REQ-USER-004)
- 담당: 김설아
- 요구사항
    ```text
    관리자 권한(Admin) 유저는 회원관리 메뉴에 접속하여 모든 회원을 목록으로 조회할 수 있다.

    목록 조회 시 검색 기능을 활용하여 이메일 혹은 이름으로 검색을 할 수 있다.

    목록 조회 시 필터 드롭다운을 적용하여 부서별 조회가 가능하다.

    목록 조회 시 확인 가능한 항목은 다음과 같다.
        • 고유 ID
        • 이메일
        • 이름
        • 부서(연구, 의료, 개발)
        • 성별(M / F)
        • 휴대폰 번호
        • 계정 활성화 여부
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 목록 조회 |
| 설명 | admin 유저가 회원 목록을 조회한다. email, name 검색과 부서 필터를 사용할 수 있다. |
| 엔드포인트(Endpoint) | `/api/v1/admin/users` |
| 메서드(Method) | GET |
| 인증 필요 여부 | Y (admin 권한만 가능) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 admin 유저의 액세스 토큰 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 요청 본문 없음 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| search | string | N | 이메일 또는 이름 검색어(일부만 입력해도 검색 가능) |
| department | string | N | 부서 필터(research, medical, develop 중 하나) |

### 3) 응답 (Response)
#### 성공
- 200 OK
```JSON
[
    {
        "id": 1,
        "email": "oz@example.com",
        "name": "김오즈",
        "department": "medical",
        "gender": "F",
        "phone_number": "010-1234-5678",
        "is_active": true
    }
]
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 고유 ID |
| email | string | 이메일 |
| name | string | 이름 |
| department | string | 부서(연구, 의료, 개발) |
| gender | string | 성별(M / F) |
| phone_number | string | 휴대폰 번호 |
| is_active | boolean | 계정 활성화 여부 |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 본문 형식 |

#### 실패
- 401 Unauthorized
```JSON
{"detail": "인증 정보가 유효하지 않습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 토큰이 없거나 만료된 경우 |

- 403 Forbidden
```JSON
{"detail": "관리자 권한이 필요합니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 어드민이 아닌 유저가 요청한 경우 |

- 422 Unprocessable Entity (부서 값이 research, medical, develop이 아닌 경우)
```JSON
{
  "detail": [
    {
      "type": "enum",
      "loc": ["query", "department"],
      "msg": "Input should be 'research', 'medical' or 'develop'",
      "input": "sales"
    }
  ]
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | array | 검증 오류 목록 |
| detail[].type | string | 오류 종류 |
| detail[].loc | array | 오류가 발생한 위치 |
| detail[].msg | string | 오류 메시지 |
| detail[].input | any | 입력된 값 |

### 4) 비고
- 어드민 권한(admin) 유저만 호출 가능
- 검색 결과가 없으면 빈 목록 `[]`을 반환(200)
- 쿼리 파라미터를 하나도 안 보내면 전체 회원 조회
- search와 department를 함께 보내면 두 조건을 모두 만족하는 회원만 조회
- 쿼리 파라미터 예시 : `/api/v1/admin/users?search=김&department=medical`


## 10. 회원 권한 변경 (REQ-USER-005)
- 담당: 김설아
- 요구사항
    ```text
    관리자 권한(Admin) 유저는 회원관리 메뉴에 접속하여 목록에서 권한 변경 대상자를 선택하고, 상단에 위치한 권한 변경 버튼클릭하여 선택된 회원의 권한을 변경할 수 있다.

    변경가능한 권한은 다음과 같다.
        • 대기자
        • 스태프
        • 어드민
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 권한 변경 |
| 설명 | admin 유저가 회원 목록에서 선택한 회원의 권한을 변경한다. |
| 엔드포인트(Endpoint) | `/api/v1/admin/users/{user_id}/role` |
| 메서드(Method) | PATCH |
| 인증 필요 여부 | Y (admin 권한만 가능) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 admin 유저의 액세스 토큰 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| user_id | integer | Y | 권한을 변경할 회원의 고유 ID |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| role | string | Y | 변경할 권한(pending, staff, admin 중 하나) |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

### 3) 응답 (Response)
#### 성공
- 200 OK
```JSON
{
    "id": 3,
    "email": "oz@example.com",
    "name": "김오즈",
    "role": "staff"
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 고유 ID |
| email | string | 이메일 |
| name | string | 이름 |
| role | string | 변경된 권한 |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 본문 형식 |

#### 실패
- 400 Bad Request (본인 권한 변경 시도)
```JSON
{"detail": "본인의 권한은 변경할 수 없습니다."}
```

- 401 Unauthorized
```JSON
{"detail": "인증 정보가 유효하지 않습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 토큰이 없거나 만료된 경우 |

- 403 Forbidden
```JSON
{"detail": "관리자 권한이 필요합니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 어드민이 아닌 유저가 요청한 경우 |

- 404 Not Found
```JSON
{"detail": "존재하지 않는 회원입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 해당 user_id의 회원이 없는 경우 |

- 422 Unprocessable Entity (권한 값이 pending, staff, admin이 아닌 경우)
```JSON
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "role"],
      "msg": "Input should be 'pending', 'staff' or 'admin'",
      "input": "manager"
    }
  ]
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | array | 검증 오류 목록 |
| detail[].type | string | 오류 종류 |
| detail[].loc | array | 오류가 발생한 위치 |
| detail[].msg | string | 오류 메시지 |
| detail[].input | any | 입력된 값 |

### 4) 비고
- 어드민 권한(admin) 유저만 호출 가능
- 한 번에 회원 한 명의 권한만 변경
- 어드민이 없어지는 상황을 막기 위해 본인 권한은 변경할 수 없음
- 변경 가능한 권한 : pending(대기자), staff(스태프), admin(어드민)
