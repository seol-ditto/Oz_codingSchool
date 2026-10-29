
from pathlib import Path

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.apis.dependencies import DBSession, StaffUser
from app.models.patients import Patient
from app.models.medical_records import MedicalRecord
from app.models.xray_images import XrayImage


router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


# ===== [시윤] 환자 정보 등록 / 환자 목록 조회 =====
# POST "" : 환자 정보 등록 (MedicalStaffUser)
# GET "" : 환자 목록 조회 (StaffUser)


# ===== [지희] 환자 정보 상세 조회 / 환자 정보 수정 =====
# GET /{patient_id} : 환자 정보 상세 조회 (StaffUser)
# PATCH /{patient_id} : 환자 정보 수정 (StaffUser)


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
