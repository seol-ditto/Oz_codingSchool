"""흉부 X-Ray 폐렴 예측 모델 (DACON 해커톤 E8_lung_crop, ResNet18)

사진 한 장이 들어와서 결과가 나가기까지
1. 공통 전처리: 흑백 → 비율 유지 224×224 (남는 부분은 검은색)
2. 검은 띠 제거: 테두리의 검은 줄을 잘라내고 다시 224×224
3. 폐 위치 찾기: 폐 분할 모델(PSPNet)로 양쪽 폐를 감싸는 상자 구하기 (못 찾으면 사진 전체)
4. 폐 영역 자르기: 폐 상자 + 8% 여백만 남겨 224×224
5. 3채널 복제 + ImageNet 정규화 → ResNet18 → 폐렴 확률
6. Grad-CAM: 모델이 폐렴이라고 판단할 때 어디를 봤는지 히트맵으로 저장

학습 때(해커톤 노트북)와 전처리가 하나라도 다르면 성능이 떨어지므로 숫자를 바꾸지 않는다.
"""

import logging
import threading
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchxrayvision as xrv
from matplotlib import colormaps
from PIL import Image
from torchvision import models, transforms

logger = logging.getLogger(__name__)

# 예측에 사용하는 모델 이름 (가중치 파일 이름과 같게)
MODEL_NAME = "E8_lung_crop"
MODEL_DIR = Path(__file__).resolve().parent / "models"

IMG_SIZE = 224          # 모델 입력 크기
BAND_THRESHOLD = 20     # 이 밝기 이하인 줄은 검은 띠로 보고 잘라냄
SEG_SIZE = 512          # 폐 분할 모델 입력 크기
LUNG_MIN_RATIO = 0.05   # 폐 픽셀이 5% 미만이면 폐를 못 찾은 것으로 보고 사진 전체 사용
LUNG_MARGIN = 0.08      # 폐 상자 바깥 여백
THRESHOLD = 0.5         # 폐렴 확률이 이 값 이상이면 폐렴으로 판정
DEVICE = "cpu"

# ImageNet 사전학습 모델에 맞춘 입력 변환 (학습 때와 동일)
TRANSFORM = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# 서버 시작 시 불러온 모델을 담아두는 곳
_models: dict = {}

# Grad-CAM은 모델에 값을 잠깐 저장해 두는 방식이라, 요청이 동시에 와도 한 번에 하나씩 예측
_lock = threading.Lock()


# ===== 1~4. 전처리 (해커톤 노트북과 동일) =====
def preprocess(img: Image.Image, size: int = IMG_SIZE) -> Image.Image:
    """공통 전처리: 흑백 → 비율 유지 축소 → 가운데 정렬 → 남는 부분 검은색"""
    img = img.convert("L")
    w, h = img.size
    s = size / max(w, h)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    if (nw, nh) != (w, h):
        img = img.resize((nw, nh), Image.BILINEAR)
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(img, ((size - nw) // 2, (size - nh) // 2))
    return canvas


def remove_band(img: Image.Image, size: int = IMG_SIZE, th: int = BAND_THRESHOLD) -> Image.Image:
    """검은 띠 제거: 가장 밝은 값이 th 이하인 줄(띠)을 잘라내고 다시 size×size"""
    arr = np.asarray(img)
    rows = np.where(arr.max(axis=1) > th)[0]
    cols = np.where(arr.max(axis=0) > th)[0]
    if len(rows) == 0 or len(cols) == 0:
        return img
    img = img.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))
    return img.resize((size, size), Image.BILINEAR)


@torch.no_grad()
def find_lung_box(img: Image.Image) -> tuple[float, float, float, float]:
    """폐 위치 찾기: 양쪽 폐를 감싸는 상자를 0~1 비율로 반환 (못 찾으면 사진 전체)"""
    seg_model = _models["seg_model"]
    arr = np.asarray(img.resize((SEG_SIZE, SEG_SIZE), Image.BILINEAR), dtype=np.float32)
    x = torch.from_numpy(xrv.datasets.normalize(arr, 255))[None, None].to(DEVICE)
    mask = (seg_model(x)[:, _models["lung_idx"]] > 0).any(1)[0].cpu().numpy()

    ys, xs = np.where(mask)
    if len(ys) < SEG_SIZE * SEG_SIZE * LUNG_MIN_RATIO:
        return (0.0, 0.0, 1.0, 1.0)
    return (xs.min() / SEG_SIZE, ys.min() / SEG_SIZE, (xs.max() + 1) / SEG_SIZE, (ys.max() + 1) / SEG_SIZE)


def crop_lung(img: Image.Image, box, margin: float = LUNG_MARGIN, size: int = IMG_SIZE) -> Image.Image:
    """폐 영역 자르기: 폐 상자 + 여백만 남겨 size×size"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    x0, x1 = max(0, x0 - w * margin), min(1, x1 + w * margin)
    y0, y1 = max(0, y0 - h * margin), min(1, y1 + h * margin)
    W, H = img.size
    img = img.crop((round(x0 * W), round(y0 * H), round(x1 * W), round(y1 * H)))
    return img.resize((size, size), Image.BILINEAR)


# ===== 6. Grad-CAM (ResNet18 layer4 기준) =====
class GradCAM:
    def __init__(self, model: nn.Module):
        self.model = model
        model.layer4.register_forward_hook(self._save_activation)

    def _save_activation(self, module, inputs, output):
        self.acts = output                              # 특징 맵
        if output.requires_grad:
            output.register_hook(self._save_grad)

    def _save_grad(self, grad):
        self.grads = grad                               # 폐렴 점수에 대한 기울기

    def compute(self, logits: torch.Tensor, size) -> np.ndarray:
        """이미 계산한 모델 출력(logits)에서 폐렴 점수로 역전파해 0~1 히트맵 반환"""
        self.model.zero_grad(set_to_none=True)
        logits[0, 1].backward()
        weights = self.grads.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self.acts).sum(dim=1, keepdim=True))
        cam = F.interpolate(cam, size=size, mode="bilinear", align_corners=False)[0, 0]
        cam = cam / (cam.max() + 1e-8)
        return cam.detach().cpu().numpy()


def overlay(img: Image.Image, cam: np.ndarray, alpha: float = 0.4) -> Image.Image:
    """흑백 사진 위에 히트맵(빨강 = 폐렴 판단에 크게 작용한 곳)을 겹친 이미지"""
    gray = np.asarray(img.convert("RGB")) / 255.0
    heat = colormaps["jet"](cam)[..., :3]
    blended = ((1 - alpha) * gray + alpha * heat).clip(0, 1)
    return Image.fromarray((blended * 255).astype(np.uint8))


# ===== 서버 시작 시 한 번만 =====
def load_models() -> None:
    """서버 시작 시(lifespan) 한 번만 호출해서 모델을 메모리에 올린다."""
    if _models:
        return

    # 분류 모델: 구조만 만들고(ImageNet 가중치 X) 저장된 가중치를 넣음
    classifier = models.resnet18(weights=None)
    classifier.fc = nn.Linear(classifier.fc.in_features, 2)   # 0: 정상, 1: 폐렴
    weight_path = MODEL_DIR / f"{MODEL_NAME}.pth"
    if not weight_path.exists():
        raise FileNotFoundError(
            f"모델 가중치가 없습니다: {weight_path} (드라이브에서 받아 worker/models/에 넣어주세요)"
        )
    state = torch.load(
        weight_path,
        map_location=DEVICE,
        weights_only=True,      # 가중치(숫자)만 불러오고 코드는 실행하지 않음 (안전한 로딩)
    )
    classifier.load_state_dict(state)
    classifier.to(DEVICE).eval()

    # 폐 분할 모델 (처음 실행할 때 인터넷에서 가중치를 받아 ~/.torchxrayvision 에 저장)
    seg_model = xrv.baseline_models.chestx_det.PSPNet().to(DEVICE).eval()
    lung_idx = [seg_model.targets.index("Left Lung"), seg_model.targets.index("Right Lung")]

    _models.update(
        classifier=classifier,
        gradcam=GradCAM(classifier),
        seg_model=seg_model,
        lung_idx=lung_idx,
    )
    logger.info("AI 모델 로딩 완료: %s", MODEL_NAME)


# ===== 예측 =====
def predict(image_path: Path, heatmap_path: Path) -> dict:
    """X-Ray 사진 한 장으로 폐렴 여부를 예측한다.

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
    if not _models:
        load_models()

    # 1~4. 전처리
    with Image.open(image_path) as img:
        base = remove_band(preprocess(img))
    box = find_lung_box(base)
    if box == (0.0, 0.0, 1.0, 1.0):
        logger.warning("폐를 찾지 못해 사진 전체로 예측: %s", image_path)
    lung = crop_lung(base, box)

    # 5. 폐렴 확률
    x = TRANSFORM(lung).unsqueeze(0).to(DEVICE)
    with _lock:
        logits = _models["classifier"](x)
        prob = torch.softmax(logits.detach(), dim=1)[0, 1].item()

        # 6. 히트맵 (실패해도 예측 결과는 돌려줌)
        saved_heatmap = None
        try:
            cam = _models["gradcam"].compute(logits, size=x.shape[-2:])
            heatmap_path = Path(heatmap_path)
            heatmap_path.parent.mkdir(parents=True, exist_ok=True)
            overlay(lung, cam).save(heatmap_path)
            saved_heatmap = str(heatmap_path)
        except Exception:
            logger.exception("히트맵 생성 실패: %s", image_path)

    is_pneumonia = prob >= THRESHOLD
    confidence = prob if is_pneumonia else 1 - prob   # 판정한 쪽의 확률

    return {
        "is_pneumonia": is_pneumonia,
        "confidence": round(confidence * 100, 2),
        "heatmap_path": saved_heatmap,
        "ai_model": MODEL_NAME,
    }
