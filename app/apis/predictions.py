from pathlib import Path

from fastapi import APIRouter, HTTPException

from worker.model import MODEL_NAME
 
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
 
 
 
# ===== [지수] 예측 결과 목록 조회 =====
# GET /medical-records/{record_id}/predictions : 예측 결과 목록 조회 (StaffUser)