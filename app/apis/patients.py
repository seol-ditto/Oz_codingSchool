from fastapi import APIRouter, Query
from sqlalchemy import select

from app.apis.dependencies import DBSession, MedicalStaffUser, StaffUser
from app.models.enums import Gender
from app.models.patients import Patient   # ★ 모델 파일 경로, 클래스 이름 확인
from app.schemas.patients import PatientCreateRequest, PatientResponse

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])

# ===== [시윤] 환자 정보 등록 / 환자 목록 조회 =====
# POST "" : 환자 정보 등록 (MedicalStaffUser)
# GET "" : 환자 목록 조회 (StaffUser)

# 환자 정보 등록 -> POST /api/v1/patients
@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    data: PatientCreateRequest,
    user: MedicalStaffUser,   # 변수를 안 써도 권한 확인(의료진 staff, admin)을 위해 필요
    db: DBSession,
):
    patient = Patient(
        name=data.name,
        age=data.age,
        gender=data.gender,
        phone=data.phone,
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)   # DB가 채운 created_at 등을 다시 가져옴
    return patient


# 환자 목록 조회 -> GET /api/v1/patients
@router.get("", response_model=list[PatientResponse])
async def get_patients(
    user: StaffUser,   # 변수를 안 써도 권한 확인(staff, admin)을 위해 필요
    db: DBSession,
    name: str | None = None,
    gender: Gender | None = None,
    min_age: int | None = Query(default=None, ge=0),
    max_age: int | None = Query(default=None, ge=0),
):
    query = select(Patient)
    if name:
        query = query.where(Patient.name.contains(name, autoescape=True))   # 이름 일부 검색
    if gender:
        query = query.where(Patient.gender == gender)
    if min_age is not None:
        query = query.where(Patient.age >= min_age)
    if max_age is not None:
        query = query.where(Patient.age <= max_age)
    query = query.order_by(Patient.id.desc())   # ★ 최신 등록순, 명세서 비고와 같아야 함

    result = await db.execute(query)
    return result.scalars().all()



# ===== [지희] 환자 정보 상세 조회 / 환자 정보 수정 =====
# GET /{patient_id} : 환자 정보 상세 조회 (StaffUser)
# PATCH /{patient_id} : 환자 정보 수정 (StaffUser)



# ===== [지수] 환자 정보 삭제 =====
# DELETE /{patient_id} : 환자 정보 삭제 (StaffUser)