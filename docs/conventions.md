# 데이터 및 모델 약속

## 저장 규칙
1. `ai_analysis_results.confidence`: 0~100 사이 퍼센트로 저장 (모델 출력 0.9753 -> 97.53). 소수점 둘째 자리까지만 저장됨
2. `xray_images.uploader_id`: 업로더가 삭제되면 NULL이 됨 (ON DELETE SET NULL). 조회 시 업로더가 없을 수 있음을 고려

## 모델 작성 규칙
1. `created_at`은 `server_default=func.now()`, `updated_at`은 `onupdate=func.now()`로 작성
2. `app/core/db/models.py`의 `TimestampMixin`은 시각이 서버 시작 시점으로 고정되는 문제가 있어 사용하지 않음
3. Enum 컬럼은 멤버 이름이 그대로 DB에 저장되므로, 멤버 이름을 ERD 값과 동일하게 작성
    - Enum 안의 `M = "M"` 한 줄을 member라고 지칭
    - 왼쪽을 name, 오른쪽을 value라고 부름

## 주어진 ERD와 다르게 구현한 부분
1. `xray_images.uploader_id`: ERD는 bigint, not null이지만 integer, nullable로 구현 (users.id 타입 일치, SET NULL 적용을 위해)