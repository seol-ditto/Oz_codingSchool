from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1", tags=["medical-records"])


# ===== [지수] 진료기록 등록 =====
# POST /patients/{patient_id}/medical-records : 진료기록 등록 (MedicalStaffUser, multipart/form-data)



# ===== [설아] 진료기록 목록 조회 / 진료기록 상세 조회 =====
from sqlalchemy import select

from app.schemas.medical_records import RecordListItemResponse, RecordDetailResponse
from app.apis.dependencies import StaffUser, DBSession
from app.models.medical_records import MedicalRecord
from app.models.xray_images import XrayImage
from app.models.patients import Patient

# ----- 진료기록 목록 조회 -----
# GET /patients/{patient_id}/medical-records : 진료기록 목록 조회 (StaffUser)
@router.get(
    "/patients/{patient_id}/medical-records",
    summary="진료기록 목록 조회 API",
    response_model=list[RecordListItemResponse],
)
async def get_medical_records(
    _: StaffUser,
    db: DBSession,
    patient_id: int,
):
    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 환자입니다."
        )

    result = await db.execute(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.created_at.desc(), MedicalRecord.id.desc())
    )
    return result.scalars().all()


# ----- 진료기록 상세 조회 -----
# GET /medical-records/{record_id} : 진료기록 상세 조회 (StaffUser)
@router.get(
    "/medical-records/{record_id}",
    summary="진료기록 상세 조회 API",
    response_model=RecordDetailResponse,
)
async def get_medical_record_detail(
    _: StaffUser,
    db: DBSession,
    record_id: int
):
    record = await db.get(MedicalRecord, record_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 진료기록입니다."
        )

    result = await db.execute(
        select(XrayImage).where(XrayImage.record_id == record_id)
    )
    xray = result.scalars().first()

    return RecordDetailResponse(
        id=record.id,
        chart_number=record.chart_number,
        symptoms=record.symptoms,
        image_url=xray.image_url,
        created_at=record.created_at,
    )