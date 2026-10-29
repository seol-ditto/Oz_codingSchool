from fastapi import APIRouter, HTTPException
from app.apis.dependencies import DBSession, StaffUser
from app.models.patients import Patient
from app.schemas.patients import PatientDetailResponse, PatientUpdateRequest


router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


# ===== [시윤] 환자 정보 등록 / 환자 목록 조회 =====
# POST "" : 환자 정보 등록 (MedicalStaffUser)
# GET "" : 환자 목록 조회 (StaffUser)



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