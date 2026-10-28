# 5일차_환자·진료기록 API 설계
## 목차
- [공통 사항 정리](#공통-사항-정리)
- [1. 환자 정보 등록 REQ-PTNT-001](#1-환자-정보-등록-req-ptnt-001)
- [2. 환자 목록 조회 REQ-PTNT-002](#2-환자-목록-조회-req-ptnt-002)
- [3. 환자 정보 상세 조회 REQ-PTNT-003](#3-환자-정보-상세-조회-req-ptnt-003)
- [4. 환자 정보 수정 REQ-PTNT-004](#4-환자-정보-수정-req-ptnt-004)
- [5. 환자 정보 삭제 REQ-PTNT-005](#5-환자-정보-삭제-req-ptnt-005)
- [6. 진료기록 등록 REQ-MDR-001](#6-진료기록-등록-req-mdr-001)
- [7. 진료기록 목록 조회 REQ-MDR-002](#7-진료기록-목록-조회-req-mdr-002)
- [8. 진료기록 상세 조회 REQ-MDR-003](#8-진료기록-상세-조회-req-mdr-003)

---

# 4조_환자·진료기록 API 명세서
## 공통 사항 정리
### 작성 규칙
- 해당 없는 칸(예: 경로 파라미터, 쿼리 파라미터, 응답 Headers)은 지우지 말고 `없음 | - | - | 없음`처럼 적기
- 실패 응답이 여러 개면 실패 블록을 복사해서 추가하기
- 인증 필요 여부는 `N (비로그인 상태에서 호출)` / `Y (로그인 필요)` / `Y (staff 이상만 가능)`처럼 적기
- 용어는 한글로 통일: 액세스 토큰, 리프레시 토큰
- 파일 업로드(X-Ray 이미지)가 있는 요청은 Content-Type이 `multipart/form-data`

### 엔드포인트(url) 규칙
- 환자: `/api/v1/patients`, 한 명은 `/api/v1/patients/{patient_id}`
- 진료기록 목록·등록: `/api/v1/patients/{patient_id}/medical-records`
- 진료기록 상세: `/api/v1/medical-records/{record_id}`

### 필드 이름
- 영어 소문자와 밑줄로 통일, **ERD 컬럼명과 동일하게** 사용
- 환자: `id, name, age, gender, phone, created_at, updated_at`
- 진료기록: `id, patient_id, chart_number, symptoms, created_at, updated_at`
- X-Ray: 요청(업로드)은 `image`(file), 응답은 `image_url`(string), 촬영 일시는 `shooting_datetime`
- **주의: 환자 연락처는 `phone`** (회원은 `phone_number`)

### 값 표기 / 입력 규칙
- 성별: `M / F` (회원과 같은 Gender 사용)
- 환자 이름: 최대 30자
- 환자 나이: 숫자 (0 이상)
- 환자 연락처: **하이픈 없이 숫자만, 최대 11자리** (예: `01012345678`)
- 진료 차트 넘버: 최대 50자, **중복 불가**
- 증상: 길이 제한 없음, 목록 조회에서는 100자 초과 시 `...`로 생략
- 날짜·시각: `2026-10-27T14:30:00` 형식

### X-Ray 이미지 규칙
- 진료기록 등록 시 이미지 파일을 함께 업로드 (진료기록 1개당 이미지 1장)
- 미리보기는 화면(브라우저)에서 처리, 별도 API 없음
- `shooting_datetime`: 선택 입력, 미입력 시 등록 시각으로 저장 (DB 필수 값이라서)
- `uploader_id`: 요청으로 받지 않고, 로그인한 유저의 id를 서버가 저장

### 삭제 규칙
- 환자 삭제 시 진료기록, X-Ray 이미지, AI 분석 결과는 DB에서 자동 삭제 (CASCADE)
- 서버에 저장된 X-Ray 이미지 **파일**은 API에서 직접 삭제

### 권한
- admin: 부서와 상관없이 모든 환자·진료기록 API 가능
    - 근거: ERD role 설명 "ADMIN: 전체 데이터 CRUD 허용"
- staff
    - 조회·수정·삭제: 가능
    - 등록(환자 정보 등록, 진료기록 등록): **부서가 medical인 경우만** 가능
    - 근거: ERD role 설명 "STAFF: 폐렴 추적 관련 데이터 CRUD 허용", 요구사항 "사내 의료인 역할을 가진 유저"
- pending: 모두 불가 (403)
    - 근거: 회원가입 명세 "pending은 마이페이지 외 접근 불가"
- 인증 필요 여부 표기
    - 조회·수정·삭제: `Y (staff 이상만 가능)`
    - 등록: `Y (의료진 staff 또는 admin만 가능)`

### 에러 형식
- 에러 메시지는 `{"detail": "메시지"}` 모양으로 한 줄로 적기
- 인증이 필요한 API 공통
    - 토큰 없음/만료/위조, 없는 회원: 401 `{"detail": "인증 정보가 유효하지 않습니다."}`
    - 비활성 회원: 403 `{"detail": "비활성화된 계정입니다."}`
    - 권한 부족(pending): 403 `{"detail": "접근 권한이 없습니다."}`
    - 의료진이 아닌 유저의 등록 시도: 403 `{"detail": "의료진만 등록할 수 있습니다."}`
- 422(필수값 누락/형식 오류)는 FastAPI가 자동으로 보내는 에러이기 때문에 아래 모양을 그대로 복사하기

```JSON
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": {}
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

### NFR-PTNT-001 / NFR-MDR-001 API 성능
- 모든 유저 API는 최대 3초 이내에 로직 처리하고 응답한다.


## 1. 환자 정보 등록 (REQ-PTNT-001)
- 담당: 홍시윤
- 요구사항
    ```text
    사내 의료인 역할을 가진 유저는 `환자 관리` 메뉴에 접속하여 `환자 정보 등록` 버튼을 클릭하여 모달을 통해 환자 정보를 시스템 상에 등록할 수 있어야 한다.

    필수 입력 항목
        • 이름
        • 나이
        • 성별
        • 연락처 ( 휴대폰 번호 )
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 등록 |
| 설명 | 이름, 나이, 성별, 연락처를 입력받아 신규 환자를 등록한다. 의료진(department가 medical인 staff) 또는 admin만 등록할 수 있다. |
| 엔드포인트(Endpoint) | `/api/v1/patients` |
| 메서드(Method) | POST |
| 인증 필요 여부 | Y (의료진 staff 또는 admin만 가능) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {액세스 토큰} | 로그인한 유저의 액세스 토큰 |
| Content-Type | application/json | 요청 본문 형식 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| name | string | Y | 환자 이름. 최대 30자 |
| age | integer	 | Y | 환자 나이. 0 이상의 숫자 |
| gender | string | Y | 성별. M / F 중 하나 |
| phone | string | Y | 환자 연락처(휴대폰 번호). 하이픈 없이 숫자만, 최대 11자리 (예: 01012345678) |

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
  "name": "김오즈",
  "age": 27,
  "gender": "F",
  "phone": "01012345678",
  "created_at": "2026-10-27T14:30:00",
  "updated_at": null
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 환자 고유 ID |
| name | string | 환자 이름 |
| age | integer | 환자 나이 |
| gender | string | 성별 (M / F) |
| phone | string | 환자 연락처 |
| created_at | string | 생성일시 (예: 2026-10-27T14:30:00) |
| updated_at | string \| null | 수정일시. 등록 직후에는 수정 이력이 없어 null |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 본문 형식 |

#### 실패
- 401 Unauthorized (토큰 없음 / 만료 / 위조, 없는 회원)
```JSON
{"detail": "인증 정보가 유효하지 않습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 403 Forbidden (비활성 회원)
```JSON
{"detail": "비활성화된 계정입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 403 Forbidden (대기자 권한: pending)
```JSON
{"detail": "접근 권한이 없습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 403 Forbidden (의료진이 아닌 staff의 등록 시도)
```JSON
{"detail": "의료진만 등록할 수 있습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 422 Unprocessable Entity (필수값 누락 / 형식 오류, FastAPI 자동 응답)
```JSON
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": {}
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
- 등록 가능한 유저: admin은 부서와 상관없이 가능, staff는 부서가 medical인 경우만 가능, pending은 불가
- 이름 30자 초과, 나이 음수, 성별이 M / F가 아닌 값, 연락처에 숫자 외 문자(하이픈 포함)가 있거나 11자리 초과인 경우 422
- 환자 등록 시 생성일시(created_at)는 서버가 저장한 등록 시각이며, 요청으로 받지 않는다.


## 2. 환자 목록 조회 (REQ-PTNT-002)
- 담당: 홍시윤
- 요구사항
    ```text
    로그인 된 사내 개발진, 의료 실무진, 연구진은 `환자 관리` 메뉴에 접속하여 의료진이 등록한 환자 정보를 목록으로 조회할 수 있다.

    목록조회시 이름을 기준으로 검색 기능을 제공한다.

    성별, 나이범위 기준의 필터링 기능을 제공한다.

    조회 가능한 필드 항목
        • 환자 고유 ID
        • 이름
        • 나이
        • 성별
        • 연락처
        • 생성일시
        • 수정일시
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 목록 조회 |
| 설명 | 등록된 환자를 목록으로 조회한다. 이름 검색, 성별 필터, 나이 범위 필터를 사용할 수 있다. |
| 엔드포인트(Endpoint) | `/api/v1/patients` |
| 메서드(Method) | GET |
| 인증 필요 여부 | Y (staff 이상만 가능) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {액세스 토큰} | 로그인한 유저의 액세스 토큰 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| name | string | N | 환자 이름 검색어 (일부만 입력해도 검색 가능) |
| gender | string | N | 성별 필터. M / F 중 하나 |
| min_age | integer | N | 나이 범위 필터의 최소 나이 (이상, 0 이상의 숫자) |
| max_age | integer | N | 나이 범위 필터의 최대 나이 (이하, 0 이상의 숫자) |

### 3) 응답 (Response)
#### 성공
- 200 OK
```JSON
[
  {
    "id": 1,
    "name": "김오즈",
    "age": 27,
    "gender": "F",
    "phone": "01012345678",
    "created_at": "2026-10-27T14:30:00",
    "updated_at": null
  }
]
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 환자 고유 ID |
| name | string | 환자 이름 |
| age | integer | 환자 나이 |
| gender | string | 성별 (M / F) |
| phone | string | 환자 연락처 |
| created_at | string | 생성일시 (예: 2026-10-27T14:30:00) |
| updated_at | string \| null | 수정일시. 수정 이력이 없으면 null |

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 본문 형식 |

#### 실패
- 401 Unauthorized (토큰 없음 / 만료 / 위조, 없는 회원)
```JSON
{"detail": "인증 정보가 유효하지 않습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 403 Forbidden (비활성 회원)
```JSON
{"detail": "비활성화된 계정입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 403 Forbidden (대기자 권한: pending)
```JSON
{"detail": "접근 권한이 없습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 422 Unprocessable Entity (쿼리 파라미터 형식 오류, FastAPI 자동 응답)
```JSON
{
  "detail": [
    {
      "type": "enum",
      "loc": ["query", "gender"],
      "msg": "Input should be 'M' or 'F'",
      "input": "X"
    }
  ]
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | array | 검증 오류 목록 |
| detail[].type | string | 검증 오류 목록 |
| detail[].loc | array | 오류가 발생한 위치 |
| detail[].msg | string | 오류 메시지 |
| detail[].input | any | 입력된 값 |


### 4) 비고
- staff, admin 모두 부서와 상관없이 조회할 수 있고, pending은 불가
- 쿼리 파라미터를 하나도 안 보내면 전체 환자를 조회
- 여러 조건을 함께 보내면 모두 만족하는 환자만 조회 (예: name과 gender를 같이 보내면 둘 다 만족)
- min_age와 max_age는 각각 단독으로도 사용 가능하며, 둘 다 보내면 그 사이(양끝 포함)의 환자만 조회
- 검색 결과가 없으면 빈 목록 []을 반환 (200)
- gender 값이 M / F가 아니거나, 나이가 숫자가 아니거나 음수인 경우 422
- 쿼리 파라미터 예시: `/api/v1/patients?name=김&gender=M&min_age=30&max_age=50`

## 3. 환자 정보 상세 조회 (REQ-PTNT-003)
- 담당: 이지희
- 요구사항
    ```text
    로그인 된 사내 개발진, 의료 실무진, 연구진은 `환자 관리` 메뉴에서 조회된 환자의 정보를 항목의 우측에 위치한 `상세보기` 버튼을 통해 상세보기 페이지로 이동하여 확인할 수 있다.

    확인 가능한 항목
        • 이름
        • 성별
        • 연락처
        • 나이
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 상세 조회 |
| 설명 | 환자 고유 ID를 이용하여 특정 환자의 상세 정보를 조회한다. |
| 엔드포인트(Endpoint) | /api/v1/patients/{patient_id} |
| 메서드(Method) | GET |
| 인증 필요 여부 | Y (staff 이상만 가능) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 유저의 액세스 토큰 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 환자 고유 ID |


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
  "id": 1,
  "name": "김오즈",
  "age": 27,
  "gender": "F",
  "phone": "01012345678",
  "created_at": "2026-10-27T14:30:00",
  "updated_at": null
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 환자 고유 ID |
| name | string | 환자 이름 |
| age | integer | 환자 나이 |
| gender | string | 환자 성별 (M/F) |
| phone | string | 환자 연락처 (하이픈 없이 숫자만) |
| created_at | string | 환자 정보 생성일시 |
| updated_at | string \| null | 환자 정보 수정일시 (수정 이력이 없으면 null) |


#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 데이터가 JSON 형식임을 나타냄 |

#### 실패
- 401 Unauthorized
```JSON
{"detail": "인증 정보가 유효하지 않습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 인증 실패 메시지 |

- 403 Forbidden (비활성 회원)
```JSON
{"detail": "비활성화된 계정입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 계정 비활성화 메시지 |

- 403 Forbidden (대기자 권한: pending)
```JSON
{"detail": "접근 권한이 없습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 접근 권한 부족 메시지 |

- 404 Not Found
```JSON
{"detail": "존재하지 않는 환자입니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 존재하지 않는 환자에 대한 오류 메시지 |

- 422 Unprocessable Entity
```JSON
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "patient_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
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
- 환자 고유 ID(patient_id)를 기준으로 특정 환자 1명의 정보를 조회한다.
- 로그인한 staff 및 admin 권한의 사용자만 조회할 수 있으며, pending 권한은 접근할 수 없다.
- patient_id가 정수가 아닌 경우 422 오류를 반환한다.

## 4. 환자 정보 수정 (REQ-PTNT-004)
- 담당: 이지희
- 요구사항
    ```text
    로그인 된 사내 개발진, 의료 실무진, 연구진은 환자 정보 상세보기 페이지 내의 우측 상단에 위치한 `정보 수정` 버튼을 클릭하여 모달을 통해 환자의 정보를 수정할 수 있다.

    수정 가능한 항목
        • 이름
        • 연락처
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 수정 |
| 설명 | 환자 고유 ID를 이용하여 특정 환자의 이름과 연락처를 수정한다. |
| 엔드포인트(Endpoint) | /api/v1/patients/{patient_id} |
| 메서드(Method) | PATCH |
| 인증 필요 여부 | Y (staff 이상만 가능) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 유저의 액세스 토큰 |
| Content-Type | application/json | 요청 본문이 JSON 형식임을 나타냄 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 환자 고유 ID |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| name | string | N | 수정할 환자 이름 (최대 30자) |
| phone | string | N | 환자 연락처. 하이픈 없이 숫자만 허용, 최대 11자리 |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |

### 3) 응답 (Response)
#### 성공
- 200 OK
```JSON
{
  "id": 1,
  "name": "김오즈",
  "age": 27,
  "gender": "F",
  "phone": "01012345678",
  "created_at": "2026-10-27T14:30:00",
  "updated_at": "2026-10-28T09:30:00"
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 환자 고유 ID |
| name | string | 환자 이름 |
| age | integer | 환자 나이 |
| gender | string | 성별 (M / F) |
| phone | string | 환자 연락처 |
| created_at | string | 생성일시 (예: 2026-10-27T14:30:00) |
| updated_at | string \| null | 수정일시. 수정 이력이 없으면 null |


#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 응답 데이터가 JSON 형식임을 나타냄 |

#### 실패

- 401 Unauthorized
```JSON
{"detail": "인증 정보가 유효하지 않습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 인증 실패 메시지 |

- 403 Forbidden (비활성 회원)
```JSON
{"detail": "비활성화된 계정입니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 계정 비활성화 메시지 |

- 403 Forbidden (대기자 권한: pending)
```JSON
{"detail": "접근 권한이 없습니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 접근 권한 부족 메시지 |

- 404 Not Found
```JSON
{"detail": "존재하지 않는 환자입니다."}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 존재하지 않는 환자에 대한 오류 메시지 |

- 422 Unprocessable Entity
```JSON
{
  "detail": [
    {
      "type": "string_too_long",
      "loc": ["body", "name"],
      "msg": "String should have at most 30 characters",
      "input": "가나다라마바사아자차카타파하가나다라마바사아자차카타파하가나다",
      "ctx": {
        "max_length": 30
      }
    }
  ]
}
```

- 422 Unprocessable Entity (경로 파라미터 patient_id가 정수가 아닌 경우)
```JSON
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "patient_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
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
| detail[].ctx | object | 검증 제한 조건 |

### 4) 비고
- 로그인한 staff 및 admin 권한의 사용자만 수정할 수 있으며, pending 권한은 접근할 수 없다.
- 이름(name)과 연락처(phone)만 부분 수정하며, 나이와 성별은 수정할 수 없다.
- 수정 성공 시 updated_at을 갱신한다.
- patient_id가 정수가 아니거나, 이름(name)이 30자를 초과하거나, 연락처(phone)에 하이픈 등 숫자 외 문자가 포함되거나 11자리를 초과하면 422 오류를 반환한다.
- 빈 JSON 객체 `{}`를 전송하면 환자 정보를 변경하지 않고 기존 정보를 200 OK로 반환한다.


## 5. 환자 정보 삭제 (REQ-PTNT-005)
- 담당: 김지수
- 요구사항
    ```text
    로그인 된 사내 개발진, 의료 실무진, 연구진은 환자 정보 상세보기 페이지 내의 우측 상단에 위치한 `삭제` 버튼을 클릭하여 모달을 통해 환자의 정보를 삭제할 수 있다.

    해당 항목의 우측에 위치한 `삭제하기` 버튼을 클릭하면 관련 데이터가 모두 삭제됨을 알리는 팝업 메시지가 노출되며 `확인했습니다` 버튼 클릭 시 해당 환자와 관련된 진료기록, X-Ray 이미지도 함께 영구 삭제한다.
    ```

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 삭제 |
| 설명 | 로그인한 사용자가 특정 환자의 정보를 삭제하며, 해당 환자의 진료기록, X-Ray 이미지 및 AI 분석 결과도 함께 삭제한다. |
| 엔드포인트(Endpoint) | `/api/v1/patients/{patient_id}` |
| 메서드(Method) | DELETE |
| 인증 필요 여부 | Y (staff 이상만 가능) |



### 2) 요청 (Request)

#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 유저의 액세스 토큰 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 삭제할 환자의 고유 ID |

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
  "message": "환자 정보가 삭제되었습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| message | string | 환자 정보 삭제 완료 메시지 |




#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | JSON 형식의 응답 |


#### 실패

- 401 Unauthorized (토큰 없음, 만료, 위조 또는 존재하지 않는 회원)

```json
{
  "detail": "인증 정보가 유효하지 않습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 인증 실패 메시지 |



- 403 Forbidden (비활성화된 회원)

```json
{
  "detail": "비활성화된 계정입니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 비활성 계정 오류 메시지 |

- 403 Forbidden (대기자 권한: pending)

```json
{
  "detail": "접근 권한이 없습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 접근 권한 부족 메시지 |



- 404 Not Found (존재하지 않는 환자)

```json
{
  "detail": "존재하지 않는 환자입니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 존재하지 않는 환자에 대한 오류 메시지 |



- 422 Unprocessable Entity (환자 ID가 숫자가 아닌 경우)

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "patient_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
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

- 권한: 로그인한 staff, admin 모두 삭제 가능하며, pending은 접근할 수 없다.
- 삭제 전 사용자에게 관련 데이터가 모두 영구 삭제됨을 알리는 확인 팝업을 표시한다. 사용자가 최종 확인한 경우에만 삭제 API를 호출한다.
- 환자 삭제 시 해당 환자의 진료기록, X-Ray 이미지 정보, AI 분석 결과는 DB의 CASCADE 설정을 통해 함께 삭제된다.
- 서버에 저장된 X-Ray 이미지 파일은 API에서 직접 삭제한다.
- 삭제된 데이터는 복구할 수 없다.
- patient_id는 정수여야 하며, 숫자가 아닌 값이 전달되면 422 오류가 발생한다.
- 환자 정보가 존재하지 않으면 404 오류를 반환한다.


## 6. 진료기록 등록 (REQ-MDR-001)
- 담당: 김지수
- 요구사항
    ```text
    사내 의료인 역할을 가진 유저는 환자 상세 정보 페이지 내의 진료 기록 목록 섹션에서 우측상단에 위치한 `진료 기록 등록` 버튼을 클릭하여 진료 기록 입력 페이지로 이동하여 환자의 X-Ray 사진을 포함한 진료기록을 시스템상에 등록할 수 있어야한다.

    환자 정보를 검색하여 환자를 선택 후 진료 정보를 기록한다.

    X-Ray 이미지 업로드 시 업로드 된 이미지의 미리보기를 제공한다.

    필수 입력 항목
        • 환자 정보 (고유 ID)
        • 진료 정보
            • 진료 차트 넘버
            • 진료된 증상
            • 촬영된 흉부 X-ray 이미지
    ```


### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 진료기록 등록 |
| 설명 | 의료진이 특정 환자의 진료 차트 번호, 증상 및 흉부 X-Ray 이미지를 등록한다. |
| 엔드포인트(Endpoint) | `/api/v1/patients/{patient_id}/medical-records` |
| 메서드(Method) | POST |
| 인증 필요 여부 | Y (의료진 staff 또는 admin만 가능) |

#
### 2) 요청 (Request)

#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 유저의 액세스 토큰 |
| Content-Type | multipart/form-data | 진료정보와 X-Ray 이미지 파일을 함께 전송 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 진료기록을 등록할 환자의 고유 ID |

#### 본문 필드
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| chart_number | string | Y | 진료 차트 번호 (최대 50자, 중복 불가) |
| symptoms | string | Y | 환자의 진료 증상 |
| image | file | Y | 촬영된 흉부 X-Ray 이미지 |
| shooting_datetime | string | N | X-Ray 촬영 일시 (예: 2026-10-28T09:00:00) |

#### 쿼리 파라미터 (GET 요청 시)
| 쿼리 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| 없음 | - | - | 없음 |


### 3) 응답 (Response)

#### 성공
- 201 Created

```json
{
  "id": 1,
  "patient_id": 1,
  "chart_number": "20261028001",
  "symptoms": "기침 및 호흡곤란",
  "image_url": "/uploads/xray/1.jpg",
  "shooting_datetime": "2026-10-28T09:00:00",
  "created_at": "2026-10-27T14:30:00",
  "updated_at": null
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 등록된 진료기록의 고유 ID |
| patient_id | integer | 환자의 고유 ID |
| chart_number | string | 진료 차트 번호 |
| symptoms | string | 환자의 진료 증상 |
| image_url | string | 업로드된 X-Ray 이미지의 접근 경로 |
| shooting_datetime | string | X-Ray 촬영 일시 |
| created_at | string | 진료기록 생성 일시 |
| updated_at | string \| null | 진료기록 수정 일시 (수정 전에는 null) |


#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 등록된 진료기록 정보를 JSON 형식으로 반환 |



#### 실패

- 401 Unauthorized (토큰 없음, 만료, 위조 또는 존재하지 않는 회원)

```json
{
  "detail": "인증 정보가 유효하지 않습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 인증 실패 메시지 |



- 403 Forbidden (비활성화된 회원)

```json
{
  "detail": "비활성화된 계정입니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 비활성 계정 오류 메시지 |

- 403 Forbidden (대기자 권한: pending)

```json
{
  "detail": "접근 권한이 없습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 접근 권한 부족 메시지 |

- 403 Forbidden (의료진이 아닌 staff의 등록 시도)

```json
{
  "detail": "의료진만 등록할 수 있습니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 의료진 권한 부족 메시지 |



- 404 Not Found (존재하지 않는 환자)

```json
{
  "detail": "존재하지 않는 환자입니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 존재하지 않는 환자에 대한 오류 메시지 |


- 409 Conflict (진료 차트 번호 중복)

```json
{
  "detail": "이미 존재하는 진료 차트 번호입니다."
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 진료 차트 번호 중복 오류 메시지 |



- 422 Unprocessable Entity (필수 입력값 누락: chart_number)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "chart_number"],
      "msg": "Field required",
      "input": {}
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

- 422 Unprocessable Entity (경로 파라미터 patient_id가 숫자가 아닌 경우)

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "patient_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
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

- 권한: admin은 부서와 관계없이 등록할 수 있으며, staff는 medical 부서인 경우에만 등록할 수 있다. pending은 접근할 수 없다.
- 진료기록 등록 시 chart_number, symptoms, image는 필수 입력값이다.
- chart_number는 최대 50자이며, 중복 등록할 수 없다.
- X-Ray 이미지는 진료기록 1개당 1장 등록한다.
- X-Ray 이미지 업로드 시 미리보기는 브라우저에서 처리하며, 별도의 미리보기 API는 제공하지 않는다.
- shooting_datetime은 선택 입력값이며, 입력하지 않으면 등록 시각으로 저장한다.
- uploader_id는 요청으로 전달받지 않고, 로그인한 사용자의 ID를 서버에서 자동으로 저장한다.
- patient_id는 정수여야 하며, 숫자가 아닌 값이 전달되면 422 오류가 발생한다.
- 필수 입력값이 누락되거나 입력 형식이 올바르지 않으면 422 오류가 발생한다.
- 존재하지 않는 환자에게 진료기록을 등록하려고 하면 404 오류를 반환한다.
- 진료기록이 정상적으로 등록되면 201 Created를 반환한다.
- 이미 등록된 진료 차트 번호로 요청하면 409 오류를 반환한다



## 7. 진료기록 목록 조회 (REQ-MDR-002)
- 담당: 김설아
- 요구사항
    ```text
    로그인 된 사내 개발진, 의료 실무진, 연구진은 환자 상세 정보 페이지 내의 진료 기록 목록 섹션에서 해당 환자의 진료기록을 목록으로 확인할 수 있다.

    조회 가능한 필드 항목
        • 진료 기록 ID
        • 진료 차트 넘버
        • 증상 (100자 초과 시 ... 생략형태)
        • 생성일시
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 진료기록 목록 조회 |
| 설명 | 환자 상세 페이지에서 해당 환자의 진료기록 목록을 조회한다. 증상은 100자 초과 시 생략해서 반환한다. |
| 엔드포인트(Endpoint) | `/api/v1/patients/{patient_id}/medical-records` |
| 메서드(Method) | GET |
| 인증 필요 여부 | Y (staff 이상만 가능) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 유저의 액세스 토큰 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 진료기록을 조회할 환자의 고유 ID |

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
[
    {
        "id": 1,
        "chart_number": "20261028001",
        "symptoms": "기침과 발열이 3일간 지속되며...",
        "created_at": "2026-10-28T14:30:00"
    }
]
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 진료기록 고유 ID |
| chart_number | string | 진료 차트 넘버 |
| symptoms | string | 증상 (100자 초과 시 앞 100자 + `...`) |
| created_at | string | 생성일시 (예: 2026-10-28T14:30:00) |

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
{"detail": "비활성화된 계정입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 계정이 비활성화된 경우 |

- 403 Forbidden
```JSON
{"detail": "접근 권한이 없습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 스태프나 어드민이 아닌 유저가 요청한 경우 |

- 404 Not Found
```JSON
{"detail": "존재하지 않는 환자입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 해당 `patient_id`의 환자가 없는 경우 |

- 422 Unprocessable Entity (`patient_id`가 숫자가 아닌 경우)
```JSON
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "patient_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
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
- staff, admin 모두 부서와 상관없이 조회 가능, pending은 불가
- 증상이 100자를 넘으면 앞 100자만 잘라 끝에 `...`을 붙여 반환(상세 조회에서는 전체 반환)
- 해당 환자의 진료기록이 없으면 빈 목록 [] 반환 (200)
- 최신 진료기록이 먼저 오도록 생성일시 내림차순 정렬


## 8. 진료기록 상세 조회 (REQ-MDR-003)
- 담당: 김설아
- 요구사항
    ```text
    로그인 된 사내 개발진, 의료 실무진, 연구진은 환자 정보 상세조회 페이지에서 조회된 진료기록 항목의 우측에 위치한 `상세보기` 버튼을 클릭하여 진료기록에 대한 상세조회를 진행할 수 있다.

    버튼 클릭 시 상세 조회 페이지로 이동한다.

    상세 조회 가능한 필드 항목
        • 진료 기록 ID
        • 차트 넘버
        • 증상
        • 흉부 X-Ray 이미지
        • 생성일시
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 진료기록 상세 조회 |
| 설명 | 진료기록 하나의 상세 정보를 흉부 X-Ray 이미지와 함께 조회한다 |
| 엔드포인트(Endpoint) | `/api/v1/medical-records/{record_id}` |
| 메서드(Method) | GET |
| 인증 필요 여부 | Y (staff 이상만 가능) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 유저의 액세스 토큰 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| record_id | integer | Y | 조회할 진료기록 고유 ID |

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
    "id": "1",
    "chart_number": "20261028001",
    "symptoms": "기침과 발열이 3일간 지속되며 호흡 시 흉통을 호소함.",
    "image_url": "https://example.com/xray/1.png",
    "created_at": "2026-10-28T14:30:00"
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 진료기록 고유 ID |
| chart_number | string | 진료 차트 넘버 |
| symptoms | string | 증상 (생략 없이 전체) |
| image_url | string | 흉부 X-Ray 이미지 URL |
| created_at | string | 생성일시 (예: 2026-10-28T14:30:00) |

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
{"detail": "비활성화된 계정입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 계정이 비활성화된 경우 |

- 403 Forbidden
```JSON
{"detail": "접근 권한이 없습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 스태프, 어드민이 아닌 유저가 요청한 경우 |

- 404 Not Found
```JSON
{"detail": "존재하지 않는 진료기록입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 해당 `record_id`의 진료기록이 없는 경우 |

- 422 Unprocessable Entity (record_id 값이 숫자가 아닌 경우)
```JSON
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "record_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
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
- staff, admin 모두 부서와 상관없이 조회 가능, pending은 불가
- 증상은 목록 조회와 달리 생략 없이 전체를 반환
- 진료기록 1개당 X-Ray 이미지는 1장이며, image_url은 해당 진료기록의 X-Ray 이미지 정보에서 가져옴
- record_id가 숫자가 아니면 422 오류를 반환
