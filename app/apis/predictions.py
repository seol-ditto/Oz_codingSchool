from app.schemas.predictions import PredictionResponse
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.dependencies import DBSession, StaffUser
from app.models.ai_analysis_results import AIAnalysisResult
from app.models.medical_records import MedicalRecord
from app.models.xray_images import XrayImage
from worker.model import MODEL_NAME, predict
 
router = APIRouter(prefix="/api/v1", tags=["predictions"])
 
 
# ===== [지희] X-Ray·히트맵 파일 경로 =====
# get_image_path(image_url: str) -> Path
#   DB의 image_url을 Path로 바꾸고, 파일이 실제로 없으면 HTTPException
# get_heatmap_path(record_id: int) -> Path
#   private_uploads/heatmaps/{record_id}_{MODEL_NAME}.png 경로를 만들어 돌려줌 (폴더 없으면 생성)

def get_image_path(image_url: str) -> Path:
    image_path = Path(image_url)

    if not image_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="X-Ray 이미지 파일을 찾을 수 없습니다."
        )

    return image_path


def get_heatmap_path(record_id: int) -> Path:
    heatmap_dir = Path("private_uploads/heatmaps")
    heatmap_dir.mkdir(parents=True, exist_ok=True)

    heatmap_path = heatmap_dir / f"{record_id}_{MODEL_NAME}.png"
    return heatmap_path
 
 
# ===== [시윤] AI 폐렴 예측 =====
# POST /medical-records/{record_id}/predictions : AI 폐렴 예측 (StaffUser)
#   진료기록 없음 404 → 같은 모델 결과 있으면 200 → 없으면 predict() 후 저장 201
 
 # 같은 진료기록, 같은 모델로 저장된 예측 결과 찾기
async def find_saved_result(db: AsyncSession, record_id: int) -> AIAnalysisResult | None:
    result = await db.execute(
        select(AIAnalysisResult).where(
            AIAnalysisResult.record_id == record_id,
            AIAnalysisResult.ai_model == MODEL_NAME,
        )
    )
    return result.scalar_one_or_none()


# AI 폐렴 예측 -> POST /api/v1/medical-records/{record_id}/predictions
@router.post(
    "/medical-records/{record_id}/predictions",
    status_code=201,
    response_model=PredictionResponse,
)
async def create_prediction(
    record_id: int,
    response: Response,
    db: DBSession,
    user: StaffUser,   # 변수를 안 써도 권한 확인(pending 차단)을 위해 필요
):
    # 1. 진료기록 확인
    record = await db.get(MedicalRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 진료기록입니다.")

    # 2. 이미 같은 모델로 예측한 결과가 있으면 AI를 다시 돌리지 않고 그대로 응답 (200)
    saved = await find_saved_result(db, record_id)
    if saved is not None:
        response.status_code = 200
        return saved

    # 3. 진료기록에 등록된 X-Ray 이미지 경로 찾기
    result = await db.execute(select(XrayImage).where(XrayImage.record_id == record_id))
    xray = result.scalars().first()
    if xray is None:
        raise HTTPException(status_code=404, detail="X-Ray 이미지 파일을 찾을 수 없습니다.")

    image_path = get_image_path(xray.image_url)    # 파일이 없으면 404
    heatmap_path = get_heatmap_path(record_id)

    # 4. AI 예측 (오래 걸리는 계산이라 서버가 멈추지 않게 별도 스레드에서 실행)
    prediction = await run_in_threadpool(predict, image_path, heatmap_path)

    # 5. 결과 저장 (히트맵을 못 만들었으면 heatmap_path가 None이라 null로 저장됨)
    new_result = AIAnalysisResult(
        record_id=record_id,
        is_pneumonia=prediction["is_pneumonia"],
        confidence=Decimal(str(round(prediction["confidence"], 2))),
        heatmap_url=prediction["heatmap_path"],
        ai_model=MODEL_NAME,
    )
    db.add(new_result)

    try:
        await db.commit()
    except IntegrityError:
        # 거의 동시에 같은 요청이 들어와 이미 저장된 경우 -> 저장된 결과를 그대로 응답 (200)
        await db.rollback()
        saved = await find_saved_result(db, record_id)
        if saved is None:
            raise
        response.status_code = 200
        return saved

    await db.refresh(new_result)
    return new_result
 
 
# ===== [지수] 예측 결과 목록 조회 =====
# GET /medical-records/{record_id}/predictions : 예측 결과 목록 조회 (StaffUser)


from sqlalchemy import select

from app.apis.dependencies import StaffUser, DBSession
from app.models.ai_analysis_results import AIAnalysisResult
from app.models.medical_records import MedicalRecord
from app.schemas.predictions import PredictionListItemResponse


@router.get(
    "/medical-records/{record_id}/predictions",
    summary="예측 결과 목록 조회 API",
    response_model=list[PredictionListItemResponse],
)
async def get_prediction_list(
    _: StaffUser,
    db: DBSession,
    record_id: int,
):
    record = await db.get(MedicalRecord, record_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="존재하지 않는 진료기록입니다.",
        )

    result = await db.execute(
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
        .order_by(
            AIAnalysisResult.created_at.desc(),
            AIAnalysisResult.id.desc(),
        )
    )

    return result.scalars().all()


# ===== [설아] 히트맵 이미지 파일 (7일차 화면 연결용) =====
# GET /medical-records/{record_id}/heatmap : 현재 모델(MODEL_NAME) 예측 결과의 히트맵 파일 응답 (StaffUser)
# X-Ray와 같은 이유로, 로그인한 직원인지 확인한 뒤에만 파일을 보내준다.
@router.get(
    "/medical-records/{record_id}/heatmap",
    summary="히트맵 이미지 파일 조회 API",
    response_class=FileResponse,
)
async def get_heatmap_image(
    _: StaffUser,
    db: DBSession,
    record_id: int,
):
    record = await db.get(MedicalRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 진료기록입니다.")

    saved = await find_saved_result(db, record_id)
    heatmap_dir = Path("private_uploads/heatmaps").resolve()
    heatmap_path = Path(saved.heatmap_url).resolve() if saved and saved.heatmap_url else None
    if (
        heatmap_path is None
        or not heatmap_path.is_relative_to(heatmap_dir)
        or not heatmap_path.is_file()
    ):
        raise HTTPException(status_code=404, detail="히트맵 이미지를 찾을 수 없습니다.")

    return FileResponse(heatmap_path)

