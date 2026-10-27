from pydantic import BaseModel, ConfigDict


# ===== [지수] 진료기록 등록 =====
# POST /patients/{patient_id}/medical-records : 진료기록 등록 (MedicalStaffUser, multipart/form-data)



# ===== [설아] 진료기록 목록 조회 / 진료기록 상세 조회 =====
# GET /patients/{patient_id}/medical-records : 진료기록 목록 조회 (StaffUser)
# GET /medical-records/{record_id} : 진료기록 상세 조회 (StaffUser)