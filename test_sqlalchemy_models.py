from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import Base, Car, Client, Mechanic, Service, ServiceOrder


def session_for_test():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_crud_and_filtering():
    session = session_for_test()
    client = Client("Алия", "+7700")
    session.add(client)
    session.commit()

    client.phone = "+7711"
    session.commit()
    stored = session.scalar(select(Client).where(Client.id == client.id))
    matches = session.scalars(
        select(Client).where(Client.name == "Алия", Client.phone == "+7711")
    ).all()

    assert stored.phone == "+7711"
    assert matches == [client]

    session.delete(client)
    session.commit()
    assert session.get(Client, client.id) is None


def test_one_to_many_and_many_to_many_relations():
    session = session_for_test()
    client = Client("Алия", "+7700")
    car = Car("Toyota", "Camry", "VIN-1", owner=client)
    mechanic = Mechanic("Алексей", "Моторист")
    service = Service("Диагностика", Decimal("3000.00"))
    session.add_all([client, car, mechanic, service])
    session.flush()

    order = ServiceOrder.create_with_services(session, car, [service], mechanic)
    session.commit()

    assert client.cars == [car]
    assert order.services == [service]
    assert order.items[0].price == Decimal("3000.00")


def test_composite_operation_is_rolled_back_with_session_transaction():
    session = session_for_test()
    car = Car("Toyota", "Camry", "VIN-2")
    service = Service("Диагностика", Decimal("3000.00"))
    session.add_all([car, service])
    session.commit()

    try:
        with session.begin():
            ServiceOrder.create_with_services(session, car, [service])
            raise RuntimeError("failure")
    except RuntimeError:
        pass

    assert session.scalars(select(ServiceOrder)).all() == []


def test_datetime_filter():
    session = session_for_test()
    car = Car("Toyota", "Camry", "VIN-3")
    session.add(car)
    session.flush()
    order = ServiceOrder(car=car)
    session.add(order)
    session.commit()

    found = session.scalars(
        select(ServiceOrder).where(ServiceOrder.created_at > datetime(2000, 1, 1))
    ).all()

    assert found == [order]
