from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ===== [시윤] 환자 정보 등록 / 환자 목록 조회 =====
# POST "" : 환자 정보 등록 (MedicalStaffUser)
# GET "" : 환자 목록 조회 (StaffUser)



# ===== [지희] 환자 정보 상세 조회 / 환자 정보 수정 =====
# GET /{patient_id} : 환자 정보 상세 조회 (StaffUser)
# PATCH /{patient_id} : 환자 정보 수정 (StaffUser)

# 환자 정보 수정 요청 -> PATCH /api/v1/patients/{patient_id}
class PatientUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=11, pattern=r"^[0-9]+$")


# 환자 정보 상세 조회 및 수정 응답
class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: str | None
    phone: str
    created_at: datetime
    updated_at: datetime | None


# ===== [지수] 환자 정보 삭제 =====
# DELETE /{patient_id} : 환자 정보 삭제 (StaffUser)