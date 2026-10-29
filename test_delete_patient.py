
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.apis.dependencies import async_get_db, get_current_staff


@pytest.fixture
def test_setup():
    # 1. 가짜 데이터베이스 만들기
    fake_db = MagicMock()
    fake_db.get = AsyncMock()
    fake_db.execute = AsyncMock()
    fake_db.delete = AsyncMock()
    fake_db.commit = AsyncMock()
    fake_db.rollback = AsyncMock()

    # 2. 가짜 로그인 사용자 만들기
    fake_user = MagicMock()
    fake_user.id = 1

    # 3. 실제 DB와 인증을 테스트용으로 대체
    app.dependency_overrides[async_get_db] = lambda: fake_db
    app.dependency_overrides[get_current_staff] = lambda: fake_user

    try:
        yield fake_db
    finally:
        app.dependency_overrides.pop(async_get_db, None)
        app.dependency_overrides.pop(get_current_staff, None)


# 1. 존재하지 않는 환자 삭제 → 404
def test_delete_patient_not_found(test_setup):
    fake_db = test_setup
    fake_db.get.return_value = None

    with TestClient(app) as client:
        response = client.delete("/api/v1/patients/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "존재하지 않는 환자입니다."

    fake_db.delete.assert_not_awaited()
    fake_db.commit.assert_not_awaited()


# 2. 정상적인 환자 삭제 → 200
def test_delete_patient_success(test_setup):
    fake_db = test_setup
    fake_patient = MagicMock(id=1)
    fake_db.get.return_value = fake_patient

    # 환자에게 연결된 X-ray 이미지가 없는 상황
    fake_result = MagicMock()
    fake_result.scalars.return_value.all.return_value = []
    fake_db.execute.return_value = fake_result

    with TestClient(app) as client:
        response = client.delete("/api/v1/patients/1")

    assert response.status_code == 200
    assert response.json() == {
        "message": "환자 정보가 삭제되었습니다."
    }

    fake_db.delete.assert_awaited_once_with(fake_patient)
    fake_db.commit.assert_awaited_once()



# 3. 환자 삭제 시 실제 X-ray 이미지 파일 삭제
def test_delete_patient_removes_xray(test_setup, tmp_path):
    fake_db = test_setup
    fake_patient = MagicMock(id=1)
    fake_db.get.return_value = fake_patient

    # 테스트용 X-ray 폴더 생성
    upload_dir = tmp_path / "private_uploads" / "xrays"
    upload_dir.mkdir(parents=True)

    # 테스트용 이미지 파일 생성
    image_path = upload_dir / "test_xray.png"
    image_path.write_bytes(b"test image data")

    assert image_path.exists()

    # 가짜 DB에 이미지 경로 등록
    fake_result = MagicMock()
    fake_result.scalars.return_value.all.return_value = [
        str(image_path)
    ]
    fake_db.execute.return_value = fake_result

    # 경로를 올바르게 연결하는 함수
    def fake_path(value):
        if value == "private_uploads/xrays":
            return upload_dir
        return Path(value)

    # 환자 삭제 API 호출
    with patch(
        "app.apis.patients.Path",
        side_effect=fake_path,
    ):
        with TestClient(app) as client:
            response = client.delete("/api/v1/patients/1")

    # 결과 확인
    assert response.status_code == 200
    assert not image_path.exists()

    fake_db.delete.assert_awaited_once_with(fake_patient)
    fake_db.commit.assert_awaited_once()



# 4. DB 삭제 실패 시 이미지 파일 유지
def test_delete_patient_db_failure(test_setup, tmp_path):
    fake_db = test_setup
    fake_patient = MagicMock(id=1)
    fake_db.get.return_value = fake_patient

    upload_dir = tmp_path / "private_uploads" / "xrays"
    upload_dir.mkdir(parents=True)

    image_path = upload_dir / "test_xray.png"
    image_path.write_bytes(b"test image data")

    fake_result = MagicMock()
    fake_result.scalars.return_value.all.return_value = [
        str(image_path)
    ]
    fake_db.execute.return_value = fake_result

    # DB 저장 중 오류 발생
    fake_db.commit.side_effect = Exception("DB 삭제 실패")

    with patch(
        "app.apis.patients.Path",
        wraps=Path,
    ) as mock_path:
        mock_path.return_value = upload_dir

        with TestClient(app) as client:
            with pytest.raises(Exception, match="DB 삭제 실패"):
                client.delete("/api/v1/patients/1")

    # DB 삭제에 실패했으므로 이미지가 남아 있어야 함
    assert image_path.exists()

    fake_db.rollback.assert_awaited_once()
    fake_db.commit.assert_awaited_once()
