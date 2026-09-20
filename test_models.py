from collections import namedtuple
from datetime import datetime
from decimal import Decimal

from models import Car, Client, OrderItem, Service, ServiceOrder
from orm import Model


Column = namedtuple("Column", "name")


def result(columns=(), one=None, many=(), rowcount=1):
    return {
        "description": [Column(name) for name in columns],
        "one": one,
        "many": many,
        "rowcount": rowcount,
    }


class FakeCursor:
    def __init__(self, results):
        self.results = iter(results)
        self.executed = []
        self.description = []
        self.current = result()
        self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=()):
        self.executed.append((query, params))
        self.current = next(self.results, result())
        self.description = self.current["description"]
        self.rowcount = self.current["rowcount"]

    def fetchone(self):
        return self.current["one"]

    def fetchall(self):
        return self.current["many"]


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_object = cursor
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self):
        return self.cursor_object

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


def test_save_creates_then_updates():
    cursor = FakeCursor([result(one=(10,)), result()])
    connection = FakeConnection(cursor)
    Model.set_connection(connection)
    client = Client("Алия", "+77001234567")

    client.save()
    client.phone = "+77007654321"
    client.save()

    assert client.id == 10
    assert cursor.executed[0][1] == ("Алия", "+77001234567")
    assert cursor.executed[1][1] == ("Алия", "+77007654321", 10)
    assert connection.commit_count == 2


def test_filter_accepts_multiple_equal_conditions_and_greater_than():
    created_at = datetime(2026, 9, 21, 10, 0)
    cursor = FakeCursor(
        [
            result(
                ("id", "name", "phone"),
                many=[(1, "Алия", "+7700")],
            ),
            result(
                ("id", "car_id", "mechanic_id", "status", "created_at"),
                many=[(2, 4, None, "new", created_at)],
            ),
        ]
    )
    Model.set_connection(FakeConnection(cursor))

    clients = Client.filter(name="Алия", phone="+7700")
    orders = ServiceOrder.filter(created_at__greater_than=datetime(2026, 9, 21, 9, 0))

    assert clients[0].name == "Алия"
    assert orders[0].created_at == created_at
    assert cursor.executed[0][1] == ("Алия", "+7700")
    assert cursor.executed[1][1] == (datetime(2026, 9, 21, 9, 0),)


def test_one_to_many_and_many_to_many_relations_map_objects():
    cursor = FakeCursor(
        [
            result(
                ("id", "make", "model", "vin", "owner_id"),
                many=[(3, "Toyota", "Camry", "VIN-3", 1)],
            ),
            result(
                ("id", "order_id", "service_id", "price"),
                many=[(8, 4, 5, Decimal("1500.00"))],
            ),
            result(
                ("id", "title", "price"),
                one=(5, "Замена масла", Decimal("1500.00")),
            ),
        ]
    )
    Model.set_connection(FakeConnection(cursor))
    client = Client("Алия", "+7700", id=1)
    order = ServiceOrder(car_id=3, id=4)

    cars = client.cars.all()
    services = order.services.all()

    assert cars[0].owner_id == client.id
    assert services[0].title == "Замена масла"


def test_composite_order_operation_uses_one_transaction():
    cursor = FakeCursor([result(one=(12,)), result(one=(13,))])
    connection = FakeConnection(cursor)
    Model.set_connection(connection)
    car = Car("Toyota", "Camry", "VIN-12", id=7)
    service = Service("Диагностика", Decimal("3000.00"), id=9)

    order = ServiceOrder.create_with_services(car, [service])

    assert order.id == 12
    assert cursor.executed[1][1] == (12, 9, Decimal("3000.00"))
    assert connection.commit_count == 1


def test_transaction_rolls_back_after_an_error():
    connection = FakeConnection(FakeCursor([]))
    Model.set_connection(connection)

    try:
        with Model.transaction():
            raise RuntimeError("failure")
    except RuntimeError:
        pass

    assert connection.rollback_count == 1
