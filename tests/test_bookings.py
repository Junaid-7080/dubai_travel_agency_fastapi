# ===== tests/test_bookings.py =====
import pytest
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

def test_create_payment_success(mocker):
    # Mock dependencies and services
    mocker.patch("main.get_current_user", return_value=type("User", (), {"id": 1, "email": "test@example.com"}))
    mock_session = mocker.MagicMock()
    mocker.patch("main.get_session", return_value=mock_session)
    mock_booking = type("Booking", (), {"id": 1, "user_id": 1, "total_price": 100.0, "booking_reference": "BR123"})
    mock_session.exec.return_value.first.side_effect = [mock_booking, None]
    mock_payment_service = mocker.patch("main.payment_service")
    mock_payment_service.process_payment.return_value = {"success": True, "client_secret": "secret"}

    payload = {
        "booking_id": 1,
        "payment_method": "STRIPE"
    }
    response = client.post("/create", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "client_secret" in response.json()["data"]
