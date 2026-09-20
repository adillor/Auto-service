from datetime import datetime

from orm import (
    DateTimeField,
    DecimalField,
    ForeignKey,
    IntegerField,
    ManyToMany,
    Model,
    OneToMany,
    StringField,
)


class Car(Model):
    id = IntegerField(primary_key=True)
    make = StringField()
    model = StringField()
    vin = StringField()
    owner_id = ForeignKey("Client", nullable=True)

    class Meta:
        table_name = "cars"

    def __init__(self, make, model, vin, owner_id=None, id=None):
        self.id = id
        self.make = make
        self.model = model
        self.vin = vin
        self.owner_id = owner_id


class Client(Model):
    id = IntegerField(primary_key=True)
    name = StringField()
    phone = StringField()
    cars = OneToMany(Car, "owner_id")

    class Meta:
        table_name = "clients"

    def __init__(self, name, phone, id=None):
        self.id = id
        self.name = name
        self.phone = phone


class Mechanic(Model):
    id = IntegerField(primary_key=True)
    name = StringField()
    specialization = StringField()

    class Meta:
        table_name = "mechanics"

    def __init__(self, name, specialization, id=None):
        self.id = id
        self.name = name
        self.specialization = specialization


class Service(Model):
    id = IntegerField(primary_key=True)
    title = StringField()
    price = DecimalField()

    class Meta:
        table_name = "services"

    def __init__(self, title, price, id=None):
        self.id = id
        self.title = title
        self.price = price


class OrderItem(Model):
    id = IntegerField(primary_key=True)
    order_id = ForeignKey("ServiceOrder")
    service_id = ForeignKey(Service)
    price = DecimalField()

    class Meta:
        table_name = "order_items"

    def __init__(self, order_id, service_id, price, id=None):
        self.id = id
        self.order_id = order_id
        self.service_id = service_id
        self.price = price


class ServiceOrder(Model):
    id = IntegerField(primary_key=True)
    car_id = ForeignKey(Car)
    mechanic_id = ForeignKey(Mechanic, nullable=True)
    status = StringField()
    created_at = DateTimeField()
    services = ManyToMany(Service, OrderItem, "order_id", "service_id")

    class Meta:
        table_name = "service_orders"

    def __init__(self, car_id, mechanic_id=None, status="new", created_at=None, id=None):
        self.id = id
        self.car_id = car_id
        self.mechanic_id = mechanic_id
        self.status = status
        self.created_at = created_at or datetime.now()

    @classmethod
    def create_with_services(cls, car, services, mechanic=None):
        mechanic_id = None if mechanic is None else mechanic.id
        with cls.transaction():
            order = cls(car_id=car.id, mechanic_id=mechanic_id).save()
            for service in services:
                order.services.add(service, price=service.price)
        return order
