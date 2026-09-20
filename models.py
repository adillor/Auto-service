"""Examples of domain models that use the shared custom ORM."""

from orm import Model


class Client(Model):
    id: int | None
    name: str
    phone: str

    class Meta:
        table_name = "clients"

    def __init__(self, name: str, phone: str, id: int | None = None):
        self.id = id
        self.name = name
        self.phone = phone


class Car(Model):
    id: int | None
    make: str
    model: str
    vin: str
    owner_id: int | None

    class Meta:
        table_name = "cars"

    def __init__(
        self,
        make: str,
        model: str,
        vin: str,
        owner_id: int | None = None,
        id: int | None = None,
    ):
        self.id = id
        self.make = make
        self.model = model
        self.vin = vin
        self.owner_id = owner_id


class Service(Model):
    id: int | None
    title: str
    price: float

    class Meta:
        table_name = "services"

    def __init__(self, title: str, price: float, id: int | None = None):
        self.id = id
        self.title = title
        self.price = price
