from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.apis.dependencies import async_get_db, get_current_staff


# 1. 가짜 데이터베이스 만들기
fake_db = MagicMock()
fake_db.get = AsyncMock(return_value=None)

# 2. 가짜 로그인 사용자 만들기
fake_user = MagicMock()

# 3. 실제 DB와 인증을 테스트용으로 대체하기
app.dependency_overrides[async_get_db] = lambda: fake_db
app.dependency_overrides[get_current_staff] = lambda: fake_user

try:
    # 4. 환자 삭제 요청 보내기
    client = TestClient(app)
    response = client.delete("/api/v1/patients/999999")

    # 5. 결과 확인하기
    print("상태 코드:", response.status_code)
    print("응답 내용:", response.json())

    assert response.status_code == 404
    print("404 테스트 성공!")

finally:
    app.dependency_overrides.clear()

    # 정상 삭제(200) 테스트

fake_patient = MagicMock(id=1)

fake_db = MagicMock()
fake_db.get = AsyncMock(return_value=fake_patient)
fake_db.delete = AsyncMock()
fake_db.commit = AsyncMock()

app.dependency_overrides[async_get_db] = lambda: fake_db
app.dependency_overrides[get_current_staff] = lambda: MagicMock()

try:
    client = TestClient(app)

    response = client.delete("/api/v1/patients/1")

    print("상태 코드:", response.status_code)
    print("응답 내용:", response.json())

    assert response.status_code == 200
    assert response.json() == {
        "message": "환자 정보가 삭제되었습니다."
    }

    fake_db.delete.assert_awaited_once_with(fake_patient)
    fake_db.commit.assert_awaited_once()

    print("200 테스트 성공!")

finally:
    app.dependency_overrides.clear()