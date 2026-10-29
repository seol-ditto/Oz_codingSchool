from pathlib import Path

# 예측에 사용하는 모델 이름 (가중치 파일 이름과 같게)
MODEL_NAME = "E8_lung_crop"

# 서버 시작 시 불러온 모델을 담아두는 곳
_models: dict = {}


def load_models() -> None:
    """
    서버 시작 시(lifespan) 한 번만 호출해서 모델을 메모리에 올린다.
    지금은 가짜라서 실제로 불러오는 것은 없다.
    """
    # TODO(설아): 실제 가중치 로딩으로 교체
    _models["ready"] = True


def predict(image_path: Path, heatmap_path: Path) -> dict:
    """
    X-Ray 사진 한 장으로 폐렴 여부를 예측한다.

    Args:
        image_path: 예측할 X-Ray 파일 경로 (DB의 image_url을 Path로 바꾼 것)
        heatmap_path: 히트맵 이미지를 저장할 경로

    Returns:
        {
            "is_pneumonia": bool,          # 폐렴이면 True
            "confidence": float,           # 판정에 대한 확신 정도 (0~100, 소수점 둘째 자리)
            "heatmap_path": str | None,    # 저장한 히트맵 경로, 실패하면 None
            "ai_model": str,               # 사용한 모델 이름
        }
    """
    # TODO(설아): 실제 모델 추론으로 교체 (지금은 항상 같은 결과)
    return {
        "is_pneumonia": True,
        "confidence": 97.53,
        "heatmap_path": str(heatmap_path),
        "ai_model": MODEL_NAME,
    }