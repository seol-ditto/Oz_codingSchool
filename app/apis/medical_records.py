<<<<<<< HEAD
=======

>>>>>>> origin/feat/patient-api-impl-jisoo
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
from app.schemas.medical_records import MedicalRecordResponse

<<<<<<< HEAD
=======

>>>>>>> origin/feat/patient-api-impl-jisoo
router = APIRouter(prefix="/api/v1", tags=["medical-records"])


# ===== [지수] 진료기록 등록 =====
# POST /patients/{patient_id}/medical-records : 진료기록 등록


@router.post(
    "/patients/{patient_id}/medical-records",
    status_code=201,
    response_model=MedicalRecordResponse,
)
async def create_medical_record(
    patient_id: int,
    db: DBSession,
    user: MedicalStaffUser,
    chart_number: Annotated[str, Form(max_length=50)],
    symptoms: Annotated[str, Form()],
    image: Annotated[UploadFile, File()],
    shooting_datetime: Annotated[datetime | None, Form()] = None,
):
    # 1. 환자 존재 여부 확인
    patient = await db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 환자입니다.",
        )

    # 2. 차트 번호 중복 확인
    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.chart_number == chart_number
        )
    )

    existing_record = result.scalar_one_or_none()

    if existing_record is not None:
        raise HTTPException(
            status_code=409,
            detail="이미 존재하는 진료 차트 번호입니다.",
        )

    # 3. 이미지 형식 확인
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

    # 4. 비공개 이미지 저장 경로
    upload_dir = Path("private_uploads/xrays")
    file_path = upload_dir / file_name

    try:
        # 5. 진료기록 생성
        new_record = MedicalRecord(
            patient_id=patient_id,
            chart_number=chart_number,
            symptoms=symptoms,
        )

        db.add(new_record)
        await db.flush()

        # 6. 이미지 검증 및 저장
        upload_dir.mkdir(parents=True, exist_ok=True)

        max_file_size = 10 * 1024 * 1024
        image_data = await image.read(max_file_size + 1)

        if len(image_data) > max_file_size:
            raise HTTPException(
                status_code=413,
                detail="이미지 파일은 10MB를 초과할 수 없습니다.",
            )

        is_png = image_data.startswith(b"\x89PNG\r\n\x1a\n")
        is_jpeg = image_data.startswith(b"\xff\xd8\xff")

        if not (is_png or is_jpeg):
            raise HTTPException(
                status_code=422,
                detail="올바른 PNG 또는 JPEG 이미지가 아닙니다.",
            )

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

        # 7. X-ray 이미지 정보 생성
        actual_shooting_datetime = shooting_datetime or datetime.now()

        new_xray = XrayImage(
            record_id=new_record.id,
            uploader_id=user.id,
            image_url=str(file_path),
            shooting_datetime=actual_shooting_datetime,
        )

        db.add(new_xray)

        # 8. DB 저장
        await db.commit()

        # 9. DB에서 생성된 날짜 등 다시 조회
        await db.refresh(new_record)

        return MedicalRecordResponse(
            id=new_record.id,
            patient_id=new_record.patient_id,
            chart_number=new_record.chart_number,
            symptoms=new_record.symptoms,
            image_url=new_xray.image_url,
            shooting_datetime=new_xray.shooting_datetime,
            created_at=new_record.created_at,
            updated_at=new_record.updated_at,
        )

    except IntegrityError:
        await db.rollback()
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=409,
            detail="이미 존재하는 진료 차트 번호입니다.",
        )

    except Exception:
        await db.rollback()
        file_path.unlink(missing_ok=True)
        raise


# ===== [설아] 진료기록 목록 조회 / 진료기록 상세 조회 =====
from sqlalchemy import select

from app.schemas.medical_records import RecordListItemResponse, RecordDetailResponse
from app.apis.dependencies import StaffUser, DBSession
from app.models.medical_records import MedicalRecord
from app.models.xray_images import XrayImage
from app.models.patients import Patient

# ----- 진료기록 목록 조회 -----
# GET /patients/{patient_id}/medical-records : 진료기록 목록 조회 (StaffUser)
<<<<<<< HEAD

=======
>>>>>>> origin/feat/patient-api-impl-jisoo
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
