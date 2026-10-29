
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.apis.dependencies import DBSession, MedicalStaffUser, StaffUser
from app.models.medical_records import MedicalRecord
from app.models.xray_images import XrayImage
from app.schemas.patients import PatientDetailResponse, PatientUpdateRequest,PatientCreateRequest, PatientResponse
from app.models.enums import Gender
from app.models.patients import Patient   # ★ 모델 파일 경로, 클래스 이름 확인

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

# 환자 정보 상세 조회
@router.get(
    "/{patient_id}",
    response_model=PatientDetailResponse,
    summary="환자 정보 상세 조회 API",
)
async def get_patient_detail(
    patient_id: int,
    db: DBSession,
    user: StaffUser,
):
    patient = await db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 환자입니다."
        )

    return patient


# 환자 정보 수정
@router.patch(
    "/{patient_id}",
    response_model=PatientDetailResponse,
    summary="환자 정보 수정 API",
)
async def update_patient(
    patient_id: int,
    data: PatientUpdateRequest,
    db: DBSession,
    user: StaffUser,
):
    patient = await db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 환자입니다."
        )

    # 실제 요청에 포함된 필드만 추출
    update_data = data.model_dump(exclude_unset=True)

    # 빈 {} 요청이면 수정하지 않고 기존 정보 반환
    if not update_data:
        return patient

    # 이름 또는 연락처 수정
    for field, value in update_data.items():
        setattr(patient, field, value)

    await db.commit()
    await db.refresh(patient)

    return patient



# ===== [지수] 환자 정보 삭제 =====
# DELETE /{patient_id} : 환자 정보 삭제 (StaffUser)
@router.delete("/{patient_id}", status_code=200)
async def delete_patient(
    patient_id: int,
    db: DBSession,
    user: StaffUser,
):
    # 1. 삭제할 환자를 찾기
    patient = await db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 환자입니다.",
        )

    # 2. 환자와 연결된 X-ray 이미지 경로 조회
    result = await db.execute(
        select(XrayImage.image_url)
        .join(
            MedicalRecord,
            XrayImage.record_id == MedicalRecord.id,
        )
        .where(MedicalRecord.patient_id == patient_id)
    )

    image_urls = result.scalars().all()

    # 3. DB에서 환자 삭제
    try:
        await db.delete(patient)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    # 4. 실제 X-ray 파일 삭제
    upload_dir = Path("private_uploads/xrays").resolve()

    for image_url in image_urls:
        if not image_url:
            continue

        image_path = Path(image_url).resolve()

        # 업로드 폴더 내부의 파일만 삭제
        if not image_path.is_relative_to(upload_dir):
            continue

        image_path.unlink(missing_ok=True)

    # 5. 삭제 완료 메시지 반환
    return {"message": "환자 정보가 삭제되었습니다."}
