from collections.abc import Generator

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from application import ApplicationError, AutoServiceApplication
from database import SessionLocal
from schemas import (
    CarCreate,
    CarResponse,
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    ServiceCreate,
    ServiceResponse,
)


app = FastAPI(title="AutoService API", version="1.0")


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def get_application(session: Session = Depends(get_session)) -> AutoServiceApplication:
    return AutoServiceApplication(session)


@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.post("/clients", response_model=ClientResponse, status_code=201)
def create_client(payload: ClientCreate, service: AutoServiceApplication = Depends(get_application)):
    return service.create_client(payload.name, payload.phone)


@app.get("/clients/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, service: AutoServiceApplication = Depends(get_application)):
    return service.get_client(client_id)


@app.patch("/clients/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, payload: ClientUpdate, service: AutoServiceApplication = Depends(get_application)):
    return service.update_client(client_id, payload.name, payload.phone)


@app.post("/cars", response_model=CarResponse, status_code=201)
def create_car(payload: CarCreate, service: AutoServiceApplication = Depends(get_application)):
    return service.create_car(payload.owner_id, payload.make, payload.model, payload.vin)


@app.post("/services", response_model=ServiceResponse, status_code=201)
def create_service(payload: ServiceCreate, service: AutoServiceApplication = Depends(get_application)):
    return service.create_service(payload.title, payload.price)


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreate, service: AutoServiceApplication = Depends(get_application)):
    return service.create_order(payload.car_id, payload.service_ids, payload.mechanic_id)


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, service: AutoServiceApplication = Depends(get_application)):
    return service.get_order(order_id)


@app.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    service: AutoServiceApplication = Depends(get_application),
):
    return service.update_order_status(order_id, payload.status)
