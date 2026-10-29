
from datetime import datetime
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.apis.dependencies import (
    async_get_db,
    get_current_medical_staff,
)


# 테스트용 PNG 이미지 생성
def make_test_png():
    image = Image.new("RGB", (2, 2), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def test_setup():
    # 가짜 데이터베이스
    fake_db = MagicMock()
    fake_db.get = AsyncMock()
    fake_db.execute = AsyncMock()
    fake_db.flush = AsyncMock()
    fake_db.commit = AsyncMock()
    fake_db.rollback = AsyncMock()
    fake_db.refresh = AsyncMock()

    # 가짜 로그인 사용자
    fake_user = MagicMock()
    fake_user.id = 1

    app.dependency_overrides[async_get_db] = lambda: fake_db
    app.dependency_overrides[get_current_medical_staff] = lambda: fake_user

    try:
        yield fake_db
    finally:
        app.dependency_overrides.pop(async_get_db, None)
        app.dependency_overrides.pop(get_current_medical_staff, None)


# 1. 존재하지 않는 환자 → 404
def test_create_medical_record_patient_not_found(test_setup):
    fake_db = test_setup
    fake_db.get.return_value = MagicMock()
    fake_db.get.return_value = None

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/patients/999999/medical-records",
            data={
                "chart_number": "TEST001",
                "symptoms": "기침",
            },
            files={
                "image": ("test.png", b"fake image", "image/png"),
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "존재하지 않는 환자입니다."


# 2. 차트 번호 중복 → 409
def test_create_medical_record_duplicate_chart(test_setup):
    fake_db = test_setup
    fake_db.get.return_value = MagicMock(id=1)

    fake_result = MagicMock()
    fake_result.scalar_one_or_none.return_value = MagicMock(id=10)
    fake_db.execute.return_value = fake_result

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/patients/1/medical-records",
            data={
                "chart_number": "CHART001",
                "symptoms": "기침",
            },
            files={
                "image": ("test.png", b"fake image", "image/png"),
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "이미 존재하는 진료 차트 번호입니다."
    )


# 3. 정상 등록 → 201
def test_create_medical_record_success(test_setup, tmp_path):
    fake_db = test_setup
    fake_db.get.return_value = MagicMock(id=1)

    fake_result = MagicMock()
    fake_result.scalar_one_or_none.return_value = None
    fake_db.execute.return_value = fake_result

    created_at = datetime(2026, 10, 29, 10, 0, 0)

    def fake_add(obj):
        if hasattr(obj, "chart_number"):
            obj.id = 100
            obj.created_at = created_at
            obj.updated_at = None

    fake_db.add.side_effect = fake_add

    with patch("app.apis.medical_records.Path") as mock_path:
        mock_path.return_value = tmp_path

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/patients/1/medical-records",
                data={
                    "chart_number": "CHART002",
                    "symptoms": "기침",
                    "shooting_datetime": "2026-10-29T10:00:00",
                },
                files={
                    "image": (
                        "test.png",
                        make_test_png(),
                        "image/png",
                    ),
                },
            )

    assert response.status_code == 201

    data = response.json()

    # 명세서에 정의된 응답 필드 8개 확인
    assert set(data.keys()) == {
        "id",
        "patient_id",
        "chart_number",
        "symptoms",
        "image_url",
        "shooting_datetime",
        "created_at",
        "updated_at",
    }

    assert data["id"] == 100
    assert data["patient_id"] == 1
    assert data["chart_number"] == "CHART002"
    assert data["symptoms"] == "기침"
    assert data["image_url"].endswith(".png")
    assert data["shooting_datetime"] == "2026-10-29T10:00:00"
    assert data["created_at"] == "2026-10-29T10:00:00"
    assert data["updated_at"] is None

    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once()

    assert len(list(tmp_path.glob("*.png"))) == 1


# 4. 이미지 용량 초과 → 413
def test_create_medical_record_image_too_large(test_setup, tmp_path):
    fake_db = test_setup
    fake_db.get.return_value = MagicMock(id=1)

    fake_result = MagicMock()
    fake_result.scalar_one_or_none.return_value = None
    fake_db.execute.return_value = fake_result

    large_image = make_test_png() + b"0" * (10 * 1024 * 1024)

    with patch("app.apis.medical_records.Path") as mock_path:
        mock_path.return_value = tmp_path

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/patients/1/medical-records",
                data={
                    "chart_number": "CHART003",
                    "symptoms": "기침",
                },
                files={
                    "image": (
                        "large.png",
                        large_image,
                        "image/png",
                    ),
                },
            )

    assert response.status_code == 413
    fake_db.rollback.assert_awaited_once()
    fake_db.commit.assert_not_awaited()
    assert list(tmp_path.iterdir()) == []


# 5. 잘못된 이미지 파일 → 422
def test_create_medical_record_invalid_image(test_setup, tmp_path):
    fake_db = test_setup
    fake_db.get.return_value = MagicMock(id=1)

    fake_result = MagicMock()
    fake_result.scalar_one_or_none.return_value = None
    fake_db.execute.return_value = fake_result

    invalid_image = b"this is not a real png image"

    with patch("app.apis.medical_records.Path") as mock_path:
        mock_path.return_value = tmp_path

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/patients/1/medical-records",
                data={
                    "chart_number": "CHART004",
                    "symptoms": "기침",
                },
                files={
                    "image": (
                        "invalid.png",
                        invalid_image,
                        "image/png",
                    ),
                },
            )

    assert response.status_code == 422
    fake_db.rollback.assert_awaited_once()
    fake_db.commit.assert_not_awaited()
    assert list(tmp_path.iterdir()) == []


# 6. DB 저장 실패 → 롤백 및 이미지 파일 삭제
def test_create_medical_record_db_failure(test_setup, tmp_path):
    fake_db = test_setup
    fake_db.get.return_value = MagicMock(id=1)

    fake_result = MagicMock()
    fake_result.scalar_one_or_none.return_value = None
    fake_db.execute.return_value = fake_result

    def fake_add(obj):
        if hasattr(obj, "chart_number"):
            obj.id = 100

    fake_db.add.side_effect = fake_add

    fake_db.commit.side_effect = IntegrityError(
        "INSERT INTO medical_records",
        {},
        Exception("DB 저장 실패"),
    )

    with patch("app.apis.medical_records.Path") as mock_path:
        mock_path.return_value = tmp_path

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/patients/1/medical-records",
                data={
                    "chart_number": "CHART005",
                    "symptoms": "기침",
                },
                files={
                    "image": (
                        "test.png",
                        make_test_png(),
                        "image/png",
                    ),
                },
            )

    assert response.status_code == 409
    fake_db.commit.assert_awaited_once()
    fake_db.rollback.assert_awaited_once()

    # DB 저장 실패 시 이미지 파일이 남아 있으면 안 됨
    assert list(tmp_path.iterdir()) == []
