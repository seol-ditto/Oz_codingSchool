
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
# GET /patients/{patient_id}/medical-records : 진료기록 목록 조회 (StaffUser)
# GET /medical-records/{record_id} : 진료기록 상세 조회 (StaffUser)
