from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, Car, Client, Service, ServiceOrder


def test_order_keeps_domain_operation_for_adding_a_service():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    client = Client("Адиль", "+7777")
    car = Car("Toyota", "Camry", "VIN1", owner=client)
    service = Service("Замена масла", Decimal("2000.00"))
    order = ServiceOrder(car=car)

    order.add_service(service)
    session.add(order)
    session.commit()

    assert order.items[0].service == service
    assert order.items[0].price == Decimal("2000.00")


def test_client_has_bidirectional_car_relation():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    client = Client("Иван", "+7111")
    car = Car("BMW", "X5", "VIN2", owner=client)

    assert car in client.cars
    assert car.owner == client
