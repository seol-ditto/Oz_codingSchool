from datetime import datetime

from pydantic import BaseModel


# ===== [지수] AI 폐렴 예측 응답 스키마 (REQ-PRED-001) =====
class PredictionResponse(BaseModel):
    is_pneumonia: bool
    confidence: float
    heatmap_url: str | None


# ===== [지수] 예측 결과 목록 응답 스키마 (REQ-PRED-002) =====
class PredictionListItemResponse(BaseModel):
    id: int
    is_pneumonia: bool
    confidence: float
    heatmap_url: str | None
    created_at: datetime
    ai_model: str