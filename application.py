from decimal import Decimal

from sqlalchemy.orm import Session

from models import Car, Client, Mechanic, Service, ServiceOrder


class ApplicationError(Exception):
    status_code = 400


class EntityNotFoundError(ApplicationError):
    status_code = 404


class OrderRuleError(ApplicationError):
    status_code = 400


class AutoServiceApplication:
    def __init__(self, session: Session):
        self.session = session

    def create_client(self, name: str, phone: str) -> Client:
        client = Client(name, phone)
        self.session.add(client)
        self.session.commit()
        return client

    def get_client(self, client_id: int) -> Client:
        client = self.session.get(Client, client_id)
        if client is None:
            raise EntityNotFoundError("Client not found")
        return client

    def update_client(self, client_id: int, name: str | None, phone: str | None) -> Client:
        client = self.get_client(client_id)
        if name is not None:
            client.name = name
        if phone is not None:
            client.phone = phone
        self.session.commit()
        return client

    def create_car(self, owner_id: int, make: str, model: str, vin: str) -> Car:
        client = self.get_client(owner_id)
        car = Car(make, model, vin, owner=client)
        self.session.add(car)
        self.session.commit()
        return car

    def create_service(self, title: str, price: Decimal) -> Service:
        service = Service(title, price)
        self.session.add(service)
        self.session.commit()
        return service

    def create_order(self, car_id: int, service_ids: list[int], mechanic_id: int | None) -> ServiceOrder:
        if not service_ids:
            raise OrderRuleError("Order must contain at least one service")
        with self.session.begin():
            car = self.session.get(Car, car_id)
            if car is None:
                raise EntityNotFoundError("Car not found")
            mechanic = None if mechanic_id is None else self.session.get(Mechanic, mechanic_id)
            if mechanic_id is not None and mechanic is None:
                raise EntityNotFoundError("Mechanic not found")
            services = [self.session.get(Service, service_id) for service_id in service_ids]
            if any(service is None for service in services):
                raise EntityNotFoundError("Service not found")
            order = ServiceOrder.create_with_services(self.session, car, services, mechanic)
        return order

    def get_order(self, order_id: int) -> ServiceOrder:
        order = self.session.get(ServiceOrder, order_id)
        if order is None:
            raise EntityNotFoundError("Order not found")
        return order

    def update_order_status(self, order_id: int, status: str) -> ServiceOrder:
        order = self.get_order(order_id)
        transitions = {
            "new": {"in_progress"},
            "in_progress": {"completed"},
            "completed": set(),
        }
        if status not in transitions.get(order.status, set()):
            raise OrderRuleError(f"Cannot change order from {order.status} to {status}")
        order.status = status
        self.session.commit()
        return order
