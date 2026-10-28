from fastapi import APIRouter, HTTPException

from app.apis.dependencies import DBSession, StaffUser
from app.models.patients import Patient

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
    # 1. 삭제할 환자를 데이터베이스에서 찾기
    patient = await db.get(Patient, patient_id)

    # 2. 환자가 존재하지 않으면 404 오류
    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 환자입니다.",
        )

    # 3. 환자 삭제
    await db.delete(patient)

    # 4. 데이터베이스에 삭제 내용 저장
    await db.commit()

    # 5. 삭제 완료 메시지 반환
    return {"message": "환자 정보가 삭제되었습니다."}