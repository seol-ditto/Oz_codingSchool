# 6일차_AI 폐렴 예측 API 설계
## 목차
- [공통 사항 정리](#공통-사항-정리)
- [1. AI 폐렴 예측 REQ-PRED-001](#1-ai-폐렴-예측-req-pred-001)
- [2. 예측 결과 목록 조회 REQ-PRED-002](#2-예측-결과-목록-조회-req-pred-002)
- [3. 히트맵 이미지 파일 조회 (7일차 화면 연결용)](#3-히트맵-이미지-파일-조회-7일차-화면-연결용)

---

# 4조_AI 폐렴 예측 API 명세서
## 공통 사항 정리
### 작성 규칙
- 해당 없는 칸(예: 경로 파라미터, 쿼리 파라미터, 응답 Headers)은 지우지 말고 `없음 | - | - | 없음`처럼 적기
- 실패 응답이 여러 개면 실패 블록을 복사해서 추가하기
- 인증 필요 여부는 `N (비로그인 상태에서 호출)` / `Y (로그인 필요)` / `Y (staff 이상만 가능)`처럼 적기
- 용어는 한글로 통일: 액세스 토큰, 리프레시 토큰
- 예측 API는 요청 본문 없이 호출 (진료기록에 등록된 X-Ray 이미지를 서버가 사용)

### 엔드포인트(url) 규칙
- 예측·예측 결과 목록: `/api/v1/medical-records/{record_id}/predictions`
    - POST: AI 폐렴 예측
    - GET: 예측 결과 목록 조회
- 히트맵 이미지 파일: `/api/v1/medical-records/{record_id}/heatmap` (7일차 화면 연결용)

### 필드 이름
- 영어 소문자와 밑줄로 통일, **ERD 컬럼명과 동일하게** 사용
- AI 폐렴 예측 응답: `is_pneumonia, confidence, heatmap_url` (요구사항의 결과 데이터 3개)
- 예측 결과 목록 응답: `id, is_pneumonia, confidence, heatmap_url, created_at, ai_model` (요구사항의 필드 항목 6개)
- **`id` 구분**
    - 응답의 `id`는 예측 결과의 고유 ID
    - 경로 파라미터 `record_id`는 진료기록의 고유 ID

### 값 표기 / 입력 규칙
- 폐렴 여부(`is_pneumonia`): 폐렴이면 `true`, 정상이면 `false`
- 신뢰도(`confidence`): AI가 내린 판정에 대한 확신 정도, 0~100 퍼센트, 소수점 둘째 자리까지 (예: `97.53`)
    - 폐렴 판정이면 폐렴일 확률, 정상 판정이면 정상일 확률 (판정 기준이 50%라서 항상 50 이상)
- 히트맵(`heatmap_url`): 히트맵 이미지 경로, 생성에 실패하면 `null`
    - 화면에서는 이 경로 대신 히트맵 이미지 파일 조회 API(3번)로 이미지를 받음
- 모델(`ai_model`): 예측에 사용한 모델 이름, 모델 가중치 파일 이름과 동일 (현재 `E8_lung_crop`)
- 날짜·시각: `2026-10-29T14:30:00` 형식

### AI 예측 규칙
- 진료기록에 등록된 X-Ray 이미지 1장으로 예측 (진료기록 1개당 이미지 1장)
- 같은 진료기록에 같은 모델로 예측한 결과가 있으면 다시 예측하지 않고 저장된 결과를 응답
    - 새로 예측: 201 Created / 저장된 결과 응답: 200 OK
- 히트맵 이미지는 X-Ray와 같은 방식으로 서버의 `private_uploads/heatmaps/`에 저장하고, DB에는 그 경로를 저장

### 삭제 규칙
- 환자·진료기록 삭제 시 AI 분석 결과는 DB에서 자동 삭제 (CASCADE)
- 서버에 저장된 히트맵 이미지 **파일**은 X-Ray 이미지 파일처럼 API에서 직접 삭제

### 권한
- admin: 부서와 상관없이 모든 예측 API 가능
    - 근거: 권한 설명 "어드민(시스템 관리자, 모든 항목에 대한 데이터 엑세스 가능)"
- staff: 부서와 상관없이 예측·목록 조회 모두 가능
    - 근거: 권한 설명 "스태프(내부 직원, 흉부 X-ray 관련 모든 읽기, 쓰기, 수정 작업 가능)"
- pending: 모두 불가 (403)
    - 근거: 권한 설명 "대기자(마이페이지 외 모든 서비스 접근 불가)"
- 인증 필요 여부 표기: `Y (staff 이상만 가능)`

### 에러 형식
- 에러 메시지는 `{"detail": "메시지"}` 모양으로 한 줄로 적기
- 인증이 필요한 API 공통
    - 토큰 없음/만료/위조, 없는 회원: 401 `{"detail": "인증 정보가 유효하지 않습니다."}`
    - 비활성 회원: 403 `{"detail": "비활성화된 계정입니다."}`
    - 권한 부족(pending): 403 `{"detail": "접근 권한이 없습니다."}`
- 없는 진료기록: 404 `{"detail": "존재하지 않는 진료기록입니다."}` (5일차와 동일)
- 422(형식 오류)는 FastAPI가 자동으로 보내는 에러이기 때문에 아래 모양을 그대로 복사하기
- 422 응답의 `ctx`(검증 제한 조건)는 글자 수 제한, enum 등 일부 오류에만 포함되며, 명세서 예시에는 생략해도 된다

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

### NFR-PRED-001 AI 모델 성능
- 평가 기준
    - Recall(민감도) ≥ 0.90 ~ 0.95 (최소 0.90): 실제 폐렴 환자를 얼마나 놓치지 않는가, TP / (TP + FN)
    - Accuracy ≥ 0.80 ~ 0.90 (보조 지표): 모델 예측 정확도, (TP + TN) / 전체 표본 수
    - 폐렴 환자를 정상으로 오진하는 FN이 가장 위험하므로 Recall을 우선으로 본다.
- 사용 모델: ResNet18 (`E8_lung_crop`)
- 평가 결과 (검증 1,044장, 해커톤 학습에 쓰지 않은 데이터)
    - Recall(민감도) 0.9742, Accuracy 0.9732 → 최소 기준(Recall 0.90), 보조 기준(Accuracy 0.80) 모두 만족
    - AUC 0.9953, FN 20장, FP 8장
- 서버 이식 확인: 검증 사진 6장(폐렴 3, 정상 3)으로 해커톤 노트북과 서버 결과 비교 → 판정과 confidence 모두 동일

### NFR-PRED-002 API 성능
- 모든 API는 3초 이내에 응답하여야 한다.
- 측정 결과 (MacBook Air CPU, 모델은 서버 시작 시 한 번만 로딩)
    - 사진 1장 예측(전처리 + 폐 위치 찾기 + 예측 + 히트맵 저장): 첫 예측 0.80초, 이후 평균 0.60초, 최대 0.68초
    - 3초 기준 통과


## 1. AI 폐렴 예측 (REQ-PRED-001)
- 담당: 홍시윤
- 요구사항
    ```text
    사내 의료인, 개발팀, 연구자 권한을 가진 유저는 진료기록 상세 페이지에서 `AI 예측 결과보기` 버튼을 클릭하여 폐렴 예측 모델을 활용한 예측결과를 확인할 수 있어야 한다.

    폐렴 예측 시 필요한 X-ray 이미지는 진료기록 저장 시 업로드한 이미지를 활용한다.

    이미 해당 진료기록으로 같은 모델을 사용하여 저장된 예측 결과가 있다면 별도로 AI 추론 과정을 거치지 않고 저장되어 있던 데이터를 응답한다.

    AI 예측 결과 섹션에서 바로 확인할 수 있도록 한다.

    결과 데이터
        • 폐렴 여부 (True, False)
        • Confidence
        • Hitmap Image URL (선택사항)
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | AI 폐렴 예측 |
| 설명 | 진료기록에 등록된 X-Ray 이미지를 AI 모델(ResNet18, E8_lung_crop)로 분석하여 폐렴 여부, 신뢰도, 히트맵 이미지 경로를 응답한다. 같은 진료기록에 같은 모델로 예측한 결과가 이미 저장되어 있으면 AI를 다시 실행하지 않고 저장된 결과를 응답한다. |
| 엔드포인트(Endpoint) | `/api/v1/medical-records/{record_id}/predictions` |
| 메서드(Method) | POST |
| 인증 필요 여부 | Y (staff 이상만 가능) |

### 2) 요청 (Request)
#### Headers
| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인한 유저의 액세스 토큰 |

#### 경로 파라미터
| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| record_id | integer | Y | 예측할 진료기록의 고유 ID |

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
- 201 Created (새로 예측하여 저장한 경우)
```JSON
{
  "is_pneumonia": true,
  "confidence": 97.53,
  "heatmap_url": "private_uploads/heatmaps/1_E8_lung_crop.png"
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| is_pneumonia | boolean | 폐렴 여부. 폐렴이면 true, 정상이면 false |
| confidence | number | AI 판정에 대한 신뢰도(0~100 퍼센트, 소수점 둘째 자리까지). 폐렴 판정이면 폐렴일 확률, 정상 판정이면 정상일 확률이라 항상 50 이상 |
| heatmap_url | string \| null | 히트맵 이미지 경로. 히트맵 생성에 실패하면 null |

- 200 OK (같은 진료기록에 같은 모델로 저장된 결과를 응답한 경우)
```JSON
{
  "is_pneumonia": true,
  "confidence": 97.53,
  "heatmap_url": "private_uploads/heatmaps/1_E8_lung_crop.png"
}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| is_pneumonia | boolean | 저장되어 있던 폐렴 여부 |
| confidence | number | 저장되어 있던 신뢰도 |
| heatmap_url | string \| null | 저장되어 있던 히트맵 이미지 경로. 없으면 null |

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

- 404 Not Found (없는 진료기록)
```JSON
{"detail": "존재하지 않는 진료기록입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 404 Not Found (진료기록의 X-Ray 이미지 파일을 찾을 수 없는 경우)
```JSON
{"detail": "X-Ray 이미지 파일을 찾을 수 없습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 422 Unprocessable Entity (record_id가 숫자가 아닌 경우)
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
- 권한: staff, admin 모두 부서와 상관없이 호출할 수 있으며, pending은 접근할 수 없다.
- 요청 본문 없이 호출하며, 진료기록 등록 때 업로드한 X-Ray 이미지(진료기록 1개당 1장)를 사용한다.
- 같은 진료기록에 같은 모델(E8_lung_crop)로 예측한 결과가 저장되어 있으면 AI를 다시 실행하지 않고 저장된 결과를 200으로 응답하며, 새로 예측하면 결과를 저장하고 201로 응답한다.
- 같은 요청이 거의 동시에 들어와도 결과는 한 번만 저장되고, 나중에 처리된 요청은 먼저 저장된 결과를 200으로 응답한다.
- 히트맵은 서버의 `private_uploads/heatmaps/`에 `{record_id}_E8_lung_crop.png`로 저장하며, 생성에 실패하면 `heatmap_url`은 `null`이고 나머지 결과는 정상 응답한다.
- 사용한 모델은 ai_model로 저장되며, 이 API의 응답에는 포함하지 않는다. (목록 조회 API에서 확인 가능)
- record_id가 숫자가 아닌 경우 422 오류를 반환한다.

## 2. 예측 결과 목록 조회 (REQ-PRED-002)
- 담당: 김지수
- 요구사항
    ```text
    사내 의료인, 개발팀, 연구자 권한을 가진 유저는 진료기록 상세 페이지의 AI 예측 결과 섹션에서 해당 환자의 흉부 X-Ray 사진과 폐렴 예측 모델을 활용한 예측결과를 목록으로 확인할 수 있어야 한다.

    목록에서 확인 가능한 필드 항목
        • 고유 ID
        • 폐렴 여부
        • Confidence
        • Hitmap Image URL
        • 예측 수행 일시
        • 사용한 모델
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 예측 결과 목록 조회 |
| 설명 | 진료기록에 저장된 AI 폐렴 예측 결과를 최신순 목록으로 조회한다. 새로 AI 예측을 실행하지 않고 저장된 결과만 읽는다. |
| 엔드포인트(Endpoint) | `/api/v1/medical-records/{record_id}/predictions` |
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
| record_id | integer | Y | 예측 결과를 조회할 진료기록의 고유 ID |

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
[
  {
    "id": 2,
    "is_pneumonia": true,
    "confidence": 97.53,
    "heatmap_url": "private_uploads/heatmaps/1_E8_lung_crop.png",
    "created_at": "2026-10-29T14:30:00",
    "ai_model": "E8_lung_crop"
  },
  {
    "id": 1,
    "is_pneumonia": false,
    "confidence": 92.15,
    "heatmap_url": null,
    "created_at": "2026-10-28T11:20:00",
    "ai_model": "다른_모델_이름"
  }
]
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 예측 결과의 고유 ID |
| is_pneumonia | boolean | 폐렴 여부. 폐렴이면 true, 정상이면 false |
| confidence | number | AI 판정에 대한 신뢰도(0~100 퍼센트, 소수점 둘째 자리까지) |
| heatmap_url | string \| null | 히트맵 이미지 경로. 히트맵 생성에 실패했으면 null |
| created_at | string | 예측 수행 일시 (예: 2026-10-29T14:30:00) |
| ai_model | string | 예측에 사용한 모델 이름 (예: E8_lung_crop) |

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

- 404 Not Found (없는 진료기록)
```JSON
{"detail": "존재하지 않는 진료기록입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 422 Unprocessable Entity (record_id가 숫자가 아닌 경우)
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
- 권한: staff, admin 모두 부서와 상관없이 호출할 수 있으며, pending은 접근할 수 없다.
- 저장된 예측 결과가 없으면 빈 목록 `[]`을 반환한다. (200 OK)
- 예측 수행 일시(`created_at`) 최신순으로 정렬하고, 일시가 같으면 `id`가 큰 것부터 보여준다.
- 같은 진료기록·같은 모델의 결과는 1개만 저장되므로, 모델이 하나인 지금은 결과가 최대 1개다. (예시의 두 번째 항목은 모델이 여러 개일 때의 모양)
- 경로의 `record_id`는 진료기록 ID이고, 응답의 `id`는 예측 결과 ID이다.
- record_id가 숫자가 아닌 경우 422 오류를 반환한다.


## 3. 히트맵 이미지 파일 조회 (7일차 화면 연결용)
- 담당: 김설아
- 요구사항
    ```text
    요구사항 없음 (7일차 화면 연결 때 추가)
    진료기록 상세 화면의 AI 예측 결과에 히트맵을 보여주기 위해 필요
    ```

### 1) API 개요
| 항목 | 내용 |
| --- | --- |
| API 이름 | 히트맵 이미지 파일 조회 |
| 설명 | 진료기록에 현재 모델(E8_lung_crop)로 저장된 예측 결과의 히트맵 이미지 파일을 응답한다. 히트맵은 서버의 private_uploads에 있어서, 로그인한 직원인지 확인한 뒤에만 보내준다. |
| 엔드포인트(Endpoint) | `/api/v1/medical-records/{record_id}/heatmap` |
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
| record_id | integer | Y | 히트맵을 조회할 진료기록의 고유 ID |

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
    - JSON이 아니라 이미지 파일 자체를 응답

#### 응답 Headers
| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Content-Type | image/png | 응답 본문 형식 (이미지 파일) |

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

- 404 Not Found (없는 진료기록)
```JSON
{"detail": "존재하지 않는 진료기록입니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 404 Not Found (예측 결과가 없거나, 히트맵이 null이거나, 파일이 없는 경우)
```JSON
{"detail": "히트맵 이미지를 찾을 수 없습니다."}
```
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| detail | string | 에러 메시지 |

- 422 Unprocessable Entity (record_id가 숫자가 아닌 경우)
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
- staff, admin 모두 부서와 상관없이 조회할 수 있으며, pending은 접근할 수 없다.
- 화면은 액세스 토큰을 붙여 이 API를 호출하고, 받은 이미지를 화면에 표시한다. (`<img src>`에 경로만 넣으면 토큰이 안 붙어서 401)
- DB의 `heatmap_url`이 `private_uploads/heatmaps/` 바깥을 가리키면 404를 반환한다.
- record_id가 숫자가 아닌 경우 422 오류를 반환한다.
