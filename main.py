from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import SessionLocal
from models import Car, Client, Mechanic, OrderItem, Service, ServiceOrder


def run_demo():
    started_at = datetime.now()
    with SessionLocal.begin() as session:
        client = Client("Сергей Петров", "+79001112233")
        car = Car("Toyota", "Camry", f"VIN-{uuid4().hex[:12]}", owner=client)
        mechanic = Mechanic("Алексей", "Моторист")
        oil = Service("Замена масла", Decimal("1500.00"))
        diagnostics = Service("Диагностика", Decimal("3000.00"))
        session.add_all([client, car, mechanic, oil, diagnostics])
        session.flush()
        order = ServiceOrder.create_with_services(session, car, [oil, diagnostics], mechanic)
        session.flush()
        client_id = client.id
        order_id = order.id

    with SessionLocal() as session:
        client = session.scalar(select(Client).where(Client.id == client_id))
        order = session.scalar(
            select(ServiceOrder)
            .where(ServiceOrder.id == order_id)
            .options(selectinload(ServiceOrder.items).selectinload(OrderItem.service))
        )
        orders = session.scalars(
            select(ServiceOrder).where(
                ServiceOrder.status == "new",
                ServiceOrder.created_at > started_at,
            )
        ).all()

        print([item.model for item in client.cars])
        print([item.title for item in order.services])
        print([item.id for item in orders])


if __name__ == "__main__":
    run_demo()
