"""Тесты для эндпоинтов API"""

from fastapi import status
from fastapi.testclient import TestClient

from app.web_main import app

client = TestClient(app)


def test_health_live_check() -> None:
    """Тест эндпоинта health/live"""
    response = client.get("/live")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ok"


def test_health_ready_check() -> None:
    """Тест эндпоинта health/ready"""
    response = client.get("/ready")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ready"


def test_predict() -> None:
    """Тест эндпоинта predict"""
    test_data = {"text": "Тестовый запрос", "max_length": 100, "temperature": 0.7}

    response = client.post("/v1/predict", json=test_data)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert "generated_text" in data
    assert isinstance(data["generated_text"], str)
    assert len(data["generated_text"]) > 0


def test_predict_invalid_input() -> None:
    """Тест эндпоинта predict с невалидными данными"""
    test_data = {"max_length": -1, "temperature": 2.0}

    response = client.post("/v1/predict", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT  # Ошибка валидации
