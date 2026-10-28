from pathlib import Path
from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.apis.dependencies import DBSession, MedicalStaffUser
from app.models.patients import Patient
from app.models.medical_records import MedicalRecord
from app.models.xray_images import XrayImage

router = APIRouter(prefix="/api/v1", tags=["medical-records"])


# ===== [지수] 진료기록 등록 =====
# POST /patients/{patient_id}/medical-records : 진료기록 등록 (MedicalStaffUser, multipart/form-data)
@router.post("/patients/{patient_id}/medical-records", status_code=201)
async def create_medical_record(
    patient_id: int,
    db: DBSession,
    user: MedicalStaffUser,
    chart_number: Annotated[str, Form(max_length=50)],
    symptoms: Annotated[str, Form()],
    image: Annotated[UploadFile, File()],
    shooting_datetime: Annotated[datetime | None, Form()] = None,
):
    # 1. 환자가 존재하는지 확인
    patient = await db.get(Patient, patient_id)

    # 2. 환자가 없으면 404 오류 반환
    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 환자입니다.",
        )

   
    # 3. 차트 번호 중복 확인
    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.chart_number == chart_number
        )
    )

    existing_record = result.scalar_one_or_none()

    # 4. 이미 등록된 차트 번호라면 409 오류 반환
    if existing_record is not None:
        raise HTTPException(
            status_code=409,
            detail="이미 등록된 차트 번호입니다.",
        )
    # 5. 업로드한 이미지 형식 확인
    allowed_types = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
    }

    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=422,
            detail="PNG 또는 JPEG 이미지만 업로드할 수 있습니다.",
        )

    extension = allowed_types[image.content_type]
    file_name = f"{uuid4().hex}{extension}"

    # 6. 비공개 이미지 저장 경로 준비
    upload_dir = Path("private_uploads/xrays")
    file_path = upload_dir / file_name

    try:
        # 7. 새로운 진료기록 생성
        new_record = MedicalRecord(
            patient_id=patient_id,
            chart_number=chart_number,
            symptoms=symptoms,
        )

        db.add(new_record)
        await db.flush()

        # 8. 이미지 파일 저장
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 이미지 최대 용량: 10MB
        max_file_size = 10 * 1024 * 1024

        # 최대 용량보다 1바이트 더 읽어서 초과 여부 확인
        image_data = await image.read(max_file_size + 1)

        if len(image_data) > max_file_size:
            raise HTTPException(
                status_code=413,
                detail="이미지 파일은 10MB를 초과할 수 없습니다.",
            )
        # 이미지 파일의 실제 시작 부분 확인
        is_png = image_data.startswith(b"\x89PNG\r\n\x1a\n")
        is_jpeg = image_data.startswith(b"\xff\xd8\xff")

        if not (is_png or is_jpeg):
            raise HTTPException(
                status_code=422,
                detail="올바른 PNG 또는 JPEG 이미지가 아닙니다.",
            )
        # 업로드된 파일 형식과 실제 파일 시작 부분 비교
        if (
            (image.content_type == "image/png" and not is_png)
            or (image.content_type == "image/jpeg" and not is_jpeg)
        ):
            raise HTTPException(
                status_code=422,
                detail="파일 형식과 실제 이미지 내용이 일치하지 않습니다.",
            )
        with open(file_path, "xb") as file:
            file.write(image_data)

        # 9. X-ray 이미지 정보 생성
        new_xray = XrayImage(
            record_id=new_record.id,
            uploader_id=user.id,
            image_url=str(file_path),
            shooting_datetime=shooting_datetime or datetime.now(),
        )

        db.add(new_xray)

        # 10. 데이터베이스 저장 확정
        await db.commit()

    except IntegrityError:
        await db.rollback()
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=409,
            detail="이미 등록된 차트 번호이거나 데이터가 충돌했습니다.",
        )

    except Exception:
        await db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    # 11. 등록 결과 반환
    return {
        "message": "진료기록이 등록되었습니다.",
        "record_id": new_record.id,
    }

# ===== [설아] 진료기록 목록 조회 / 진료기록 상세 조회 =====
# GET /patients/{patient_id}/medical-records : 진료기록 목록 조회 (StaffUser)
# GET /medical-records/{record_id} : 진료기록 상세 조회 (StaffUser)