class DomainError(Exception):
    """Базовое исключение для ошибок предметной области автосервиса."""
    pass


class InvalidStatusError(DomainError):
    """Исключение при попытке выполнить недопустимую операцию для текущего статуса."""
    pass


class OrderValidationError(DomainError):
    """Исключение при попытке запустить заказ без выполнения бизнес-условий."""
    pass


class Client:
    def __init__(self, name: str, phone: str):
        self.name = name
        self.phone = phone

    def __str__(self):
        return f"Клиент {self.name} телефон:{self.phone}"


class Car:
    def __init__(self, make: str, model: str, vin: str, owner: Client = None):
        self.make = make
        self.model = model
        self.vin = vin
        self.owner = owner

    def __str__(self):
        owner_name = self.owner.name if self.owner else "Нет владельца"
        return f"Авто: {self.make} {self.model} [{self.vin}] — Владелец: {owner_name}"


class Mechanic:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    def __str__(self):
        return f"Механик: {self.name} (специализация: {self.role})"


class Service:
    def __init__(self, title: str, base_price: float):
        self.title = title
        self.base_price = base_price

    def __str__(self):
        return f"Услуга: {self.title} — {self.base_price}."


class Order_item:
    def __init__(self, service: Service, price: float = None, quantity: int = 1):
        self.service = service
        self.price = price if price is not None else service.base_price
        self.quantity = quantity

    def __str__(self):
        total = self.price * self.quantity
        return f"Позиция: {self.service.title} x{self.quantity} = {total}."


class Service_order:
    def __init__(self, order_id: int, car: Car, mechanic: Mechanic = None):
        self.order_id = order_id
        self.car = car
        self.mechanic = mechanic
        self.status = "new"
        self.items = []

    def assign_mechanic(self, mechanic: Mechanic):
        if self.status == "completed":
            raise InvalidStatusError("Нельзя менять механика в завершённом заказе!")
        self.mechanic = mechanic

    def add_item(self, item: Order_item):
        if self.status == "completed":
            raise InvalidStatusError("Нельзя добавлять услуги в завершённый заказ!")
        self.items.append(item)

    def start_order(self):
        if self.status != "new":
            raise InvalidStatusError("Запустить можно только новый заказ!")
        if not self.mechanic:
            raise OrderValidationError("Нельзя запустить заказ без назначенного механика!")
        if not self.items:
            raise OrderValidationError("Нельзя запустить пустой заказ!")
        self.status = "in_progress"

    def complete_order(self):
        if self.status != "in_progress":
            raise InvalidStatusError("Завершить можно только заказ, находящийся в работе!")
        self.status = "completed"

    def calculate_total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)

    def __str__(self):
        mech_str = self.mechanic.name if self.mechanic else "Не назначен"
        return f"Заказ №{self.order_id} [{self.status}] | Авто: {self.car.make} {self.car.model} | Механик: {mech_str} | Итого: {self.calculate_total()} руб."


if __name__ == "__main__":
    print("=== УСПЕШНЫЙ СЦЕНАРИЙ OBSLUZHIVANIYA ===")
    
    client1 = Client("adil", "+7-777-777-77-77")
    client2 = Client("ООО Adil", "+7-777-777-77-67")

    car1 = Car("Toyota", "Camry", "А123АА777", client1)
    car2 = Car("GAZ", "Gazelle", "В456ВВ777", client2)

    mechanic1 = Mechanic("Алексей", "Моторист")

    service1 = Service("Замена масла", 1500.0)
    service2 = Service("Диагностика двигателя", 2000.0)

    item1 = Order_item(service1, quantity=1)
    item2 = Order_item(service2, quantity=1)

    order1 = Service_order(order_id=1, car=car1)
    print(f"1. Создан заказ: {order1}")

    order1.assign_mechanic(mechanic1)
    order1.add_item(item1)
    order1.add_item(item2)
    print(f"2. Назначен механик и добавлены услуги: {order1}")

    order1.start_order()
    print(f"3. Заказ запущен в работу: {order1}")

    order1.complete_order()
    print(f"4. Заказ успешно завершён: {order1}\n")

    print("=== ДЕМОНСТРАЦИЯ ЗАПРЕЩЁННЫХ ОПЕРАЦИЙ ===")

    order2 = Service_order(order_id=2, car=car2)
    try:
        print("Попытка запустить пустой заказ...")
        order2.start_order()
    except OrderValidationError as e:
        print(f" [БЛОКИРОВКА]: {e}")

    order2.add_item(item1)
    try:
        print("Попытка запустить заказ без механика...")
        order2.start_order()
    except OrderValidationError as e:
        print(f" [БЛОКИРОВКА]: {e}")

    try:
        print("Попытка добавить услугу в завершённый заказ №1...")
        order1.add_item(item1)
    except InvalidStatusError as e:
        print(f" [БЛОКИРОВКА]: {e}")

    try:
        print("Попытка повторно запустить закрытый заказ №1...")
        order1.start_order()
    except InvalidStatusError as e:
        print(f" [БЛОКИРОВКА]: {e}")