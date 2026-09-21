from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api import app, get_session
from models import Base


def api_client():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session():
        with test_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    return TestClient(app)


def test_client_crud_and_order_business_flow():
    client = api_client()
    created_client = client.post("/clients", json={"name": "Алия", "phone": "+7700"})
    assert created_client.status_code == 201
    client_id = created_client.json()["id"]

    updated_client = client.patch(f"/clients/{client_id}", json={"phone": "+7711"})
    assert updated_client.status_code == 200
    assert updated_client.json()["phone"] == "+7711"

    car = client.post(
        "/cars",
        json={"owner_id": client_id, "make": "Toyota", "model": "Camry", "vin": "API-VIN-1"},
    )
    service = client.post("/services", json={"title": "Диагностика", "price": "3000.00"})
    assert car.status_code == 201
    assert service.status_code == 201

    order = client.post(
        "/orders",
        json={"car_id": car.json()["id"], "service_ids": [service.json()["id"]]},
    )
    assert order.status_code == 201
    order_id = order.json()["id"]

    started = client.patch(f"/orders/{order_id}/status", json={"status": "in_progress"})
    completed = client.patch(f"/orders/{order_id}/status", json={"status": "completed"})
    assert started.status_code == 200
    assert completed.json()["status"] == "completed"


def test_api_returns_validation_and_domain_errors():
    client = api_client()

    invalid_payload = client.post("/clients", json={"name": "", "phone": ""})
    absent_client = client.get("/clients/999")
    absent_car = client.post("/orders", json={"car_id": 999, "service_ids": [1]})

    assert invalid_payload.status_code == 422
    assert absent_client.status_code == 404
    assert absent_car.status_code == 404
