from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Gender

# ===== [시윤] 환자 정보 등록 / 환자 목록 조회 =====
# POST "" : 환자 정보 등록 (MedicalStaffUser)
# GET "" : 환자 목록 조회 (StaffUser)

# 환자 정보 등록 요청 -> POST /api/v1/patients
class PatientCreateRequest(BaseModel):
    name: str = Field(max_length=30)
    age: int = Field(ge=0)
    gender: Gender
    phone: str = Field(pattern=r"^\d{1,11}$")   # 하이픈 없이 숫자만, 최대 11자리

# 환자 응답 (환자 1명분) -> POST /api/v1/patients, GET /api/v1/patients
class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: Gender | None
    phone: str
    created_at: datetime
    updated_at: datetime | None



# ===== [지희] 환자 정보 상세 조회 / 환자 정보 수정 =====
# GET /{patient_id} : 환자 정보 상세 조회 (StaffUser)
# PATCH /{patient_id} : 환자 정보 수정 (StaffUser)

# 환자 정보 수정 요청 -> PATCH /api/v1/patients/{patient_id}
class PatientUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=11, pattern=r"^[0-9]+$")

    @field_validator("name", "phone")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("null은 입력할 수 없습니다.")
        return value


# 환자 정보 상세 조회 및 수정 응답
class PatientDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    age: int
    gender: str | None
    phone: str



# ===== [지수] 환자 정보 삭제 =====
# DELETE /{patient_id} : 환자 정보 삭제 (StaffUser)