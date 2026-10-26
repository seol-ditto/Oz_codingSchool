# 3일차_ DB 모델 작성 및 마이그레이션
## 작업 내용
- ERD를 확인한 후, 각자 테이블을 맡아 SQLAlchemy로 `app/models` 폴더 안에 `테이블명.py` 모델 작성
- 모델 작성 완료 후 `app/models/__init__.py` 에 `import``
- MySQL 설치 후 alembic으로 마이그레이션 진행

## DB
- DBMS: MySQL (DB명: `ai_health`)
- `app/core/config.py`를 보고 setting 설정

## 실행 순서
```bash
uv run alembic revision --autogenerate -m "create initial tables"
```
- 생성된 `alembic/versions/새로생성된파일.py` 확인
    - 각 모델의 `create_table`이 다 있는지
    - FK 부분에 `ondelete='CASCADE', ondelete='SET NULL'` 들어있는지
    - `uploader_id`가 `nullable=True`인지
```bash
uv run alembic upgrade head
uv run alembic current         # 버전 번호 옆에 (head) 떠있는지 확인
```

## DB Viewer로 실제 생성된 DB 확인(DBeaver 사용)
### Database ERD 확인
![DB SCHEMA](images/Day3_ERD.png)

### 각 테이블 별 Columns 확인
#### 1. ai_analysis_results
![ai_analysis_results](images/Day3_ai_analysis_results.png)
#### 2. medical_records
![medical_records](images/Day3_medical_records.png)
#### 3. patients
![patients](images/Day3_patients.png)
#### 4. users
![users](images/Day3_users.png)
#### 5. xray_images
![xray_images](images/Day3_xray_images.png)