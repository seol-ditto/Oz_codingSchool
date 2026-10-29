
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


# ===== [지수] 진료기록 등록 =====
# POST /patients/{patient_id}/medical-records : 진료기록 등록


class MedicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    chart_number: str
    symptoms: str
    image_url: str
    shooting_datetime: datetime
    created_at: datetime
    updated_at: datetime | None


# ===== [설아] 진료기록 목록 조회 / 진료기록 상세 조회 =====
# ------ 진료 기록 목록 조회 ------
# GET /patients/{patient_id}/medical-records : 진료기록 목록 조회 (StaffUser)
class RecordListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chart_number: str
    symptoms: str
    created_at: datetime

    # 증상이 100자 초과하면 생략하고 `...` 붙이기
    @field_validator("symptoms")
    @classmethod
    def shorten_symptom(cls, symptoms):
        if len(symptoms) > 100:
            return symptoms[:100] + "..."

        return symptoms


# ------ 진료 기록 상세 조회 ------
# GET /medical-records/{record_id} : 진료기록 상세 조회 (StaffUser)
class RecordDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chart_number: str
    symptoms: str
    image_url: str
    created_at: datetime