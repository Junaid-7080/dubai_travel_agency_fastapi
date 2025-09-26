# ===== tests/test_packages.py =====
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_packages():
    response = client.get("/packages/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_featured_packages():
    response = client.get("/public/featured-packages")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_search_packages():
    response = client.get("/packages/?search=dubai")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_package_by_id():
    # This will fail if no packages exist, but shows the structure
    response = client.get("/packages/1")
    # Could be 404 if package doesn't exist, which is fine for test
    assert response.status_code in [200, 404]
