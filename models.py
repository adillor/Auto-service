from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(50))
    cars: Mapped[list[Car]] = relationship(back_populates="owner")

    def __init__(self, name: str, phone: str):
        self.name = name
        self.phone = phone


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    make: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    vin: Mapped[str] = mapped_column(String(100), unique=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True)
    owner: Mapped[Client | None] = relationship(back_populates="cars")
    orders: Mapped[list[ServiceOrder]] = relationship(back_populates="car")

    def __init__(self, make: str, model: str, vin: str, owner: Client | None = None):
        self.make = make
        self.model = model
        self.vin = vin
        self.owner = owner


class Mechanic(Base):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    specialization: Mapped[str] = mapped_column(String(100))
    orders: Mapped[list[ServiceOrder]] = relationship(back_populates="mechanic")

    def __init__(self, name: str, specialization: str):
        self.name = name
        self.specialization = specialization


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    order_items: Mapped[list[OrderItem]] = relationship(back_populates="service")

    def __init__(self, title: str, price: Decimal):
        self.title = title
        self.price = price


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"))
    mechanic_id: Mapped[int | None] = mapped_column(ForeignKey("mechanics.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now())
    car: Mapped[Car] = relationship(back_populates="orders")
    mechanic: Mapped[Mechanic | None] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(back_populates="order", cascade="all, delete-orphan")
    services = association_proxy(
        "items",
        "service",
        creator=lambda service: OrderItem(service=service, price=service.price),
    )

    def __init__(self, car: Car, mechanic: Mechanic | None = None, status: str = "new"):
        self.car = car
        self.mechanic = mechanic
        self.status = status

    def add_service(self, service: Service, price: Decimal | None = None) -> None:
        self.items.append(OrderItem(service=service, price=service.price if price is None else price))

    @classmethod
    def create_with_services(
        cls,
        session: Session,
        car: Car,
        services: list[Service],
        mechanic: Mechanic | None = None,
    ) -> ServiceOrder:
        order = cls(car=car, mechanic=mechanic)
        session.add(order)
        for service in services:
            order.add_service(service)
        return order


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("service_orders.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    order: Mapped[ServiceOrder] = relationship(back_populates="items")
    service: Mapped[Service] = relationship(back_populates="order_items")

    def __init__(self, service: Service, price: Decimal):
        self.service = service
        self.price = price
