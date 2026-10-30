"""서버 없이 AI 모델만 확인하는 스크립트

실행 (프로젝트 맨 위 폴더에서):
    uv run python -m worker.check_model 사진1.png 사진2.jpg ...

확인하는 것
1. 모델 로딩 시간 (서버 시작 시 한 번)
2. 사진별 예측 결과와 걸린 시간 (첫 예측 / 이후 예측) → NFR-PRED-002 3초 기준
3. 히트맵 저장 위치 (worker/check_outputs/, 커밋하지 않음)
"""

import sys
import time
from pathlib import Path

from worker.model import MODEL_NAME, load_models, predict

OUT_DIR = Path(__file__).resolve().parent / "check_outputs"


def main(paths: list[str]) -> None:
    if not paths:
        print("사용법: uv run python -m worker.check_model 사진1.png 사진2.jpg ...")
        return

    start = time.perf_counter()
    load_models()
    print(f"모델 로딩 ({MODEL_NAME}): {time.perf_counter() - start:.2f}초\n")

    times = []
    for path in paths:
        start = time.perf_counter()
        result = predict(Path(path), OUT_DIR / f"{Path(path).stem}_heatmap.png")
        elapsed = time.perf_counter() - start
        times.append(elapsed)

        label = "폐렴" if result["is_pneumonia"] else "정상"
        print(f"{Path(path).name}: {label}, confidence {result['confidence']}, {elapsed:.2f}초")
        print(f"    히트맵: {result['heatmap_path']}")

    print(f"\n첫 예측: {times[0]:.2f}초")
    if len(times) > 1:
        rest = times[1:]
        print(f"이후 예측: 평균 {sum(rest) / len(rest):.2f}초, 최대 {max(rest):.2f}초")
    print("3초 기준:", "통과" if max(times) < 3 else "초과")


if __name__ == "__main__":
    main(sys.argv[1:])
