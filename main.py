from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import psycopg

from models import Car, Client, Mechanic, Service, ServiceOrder
from orm import Model

DB_PARAMS = "dbname=autoservice user=postgres password=postgres host=127.0.0.1 port=5432 connect_timeout=5"


def run_demo():
    with psycopg.connect(DB_PARAMS) as connection:
        Model.set_connection(connection)
        started_at = datetime.now()
        client = Client("Сергей Петров", "+79001112233").save()
        car = Car("Toyota", "Camry", f"VIN-{uuid4().hex[:12]}", owner_id=client.id).save()
        mechanic = Mechanic("Алексей", "Моторист").save()
        oil = Service("Замена масла", Decimal("1500.00")).save()
        diagnostics = Service("Диагностика", Decimal("3000.00")).save()
        order = ServiceOrder.create_with_services(car, [oil, diagnostics], mechanic)

        print([item.model for item in client.cars.all()])
        print([item.title for item in order.services.all()])
        print([item.id for item in ServiceOrder.filter(status="new", created_at__greater_than=started_at)])


if __name__ == "__main__":
    run_demo()
