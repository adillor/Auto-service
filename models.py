from abc import ABC, abstractmethod


class DomainError(Exception):
    pass


class InvalidStatusError(DomainError):
    pass


class OrderValidationError(DomainError):
    pass


class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, amount: float) -> float:
        pass


class NoDiscount(DiscountStrategy):
    def calculate(self, amount: float) -> float:
        return 0.0


class PercentageDiscount(DiscountStrategy):
    def __init__(self, percent: float):
        if not (0 <= percent <= 100):
            raise DomainError("Некорректный процент скидки")
        self.percent = percent

    def calculate(self, amount: float) -> float:
        return amount * (self.percent / 100.0)


class FixedDiscount(DiscountStrategy):
    def __init__(self, discount_amount: float):
        if discount_amount < 0:
            raise DomainError("Скидка не может быть отрицательной")
        self.discount_amount = discount_amount

    def calculate(self, amount: float) -> float:
        return min(amount, self.discount_amount)


class ThresholdDiscount(DiscountStrategy):
    def __init__(self, threshold: float, percent: float):
        self.threshold = threshold
        self.percent = percent

    def calculate(self, amount: float) -> float:
        if amount >= self.threshold:
            return amount * (self.percent / 100.0)
        return 0.0


class Client:
    def __init__(self, name: str, phone: str):
        self.name = name
        self.phone = phone
        self.cars = []

    def add_car(self, car: 'Car'):
        if car in self.cars:
            raise DomainError(f"Авто {car.vin} уже привязано к клиенту {self.name}.")

        if car.owner and car.owner != self:
            car.owner.remove_car(car)

        self.cars.append(car)
        car.owner = self

    def remove_car(self, car: 'Car'):
        if car not in self.cars:
            raise DomainError(f"Авто {car.vin} не принадлежит клиенту {self.name}.")
        self.cars.remove(car)
        car.owner = None

    def __str__(self):
        return f"Клиент {self.name} телефон:{self.phone}"


class Car:
    def __init__(self, make: str, model: str, vin: str, owner: Client = None):
        self.make = make
        self.model = model
        self.vin = vin
        self.owner = None
        if owner:
            owner.add_car(self)

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


class OrderItem:
    def __init__(self, service: Service, price: float = None, quantity: int = 1):
        self.service = service
        self.price = price if price is not None else service.base_price
        self.quantity = quantity

    def __str__(self):
        total = self.price * self.quantity
        return f"Позиция: {self.service.title} x{self.quantity} = {total}."


class ServiceOrder:
    def __init__(self, order_id: int, car: Car, mechanic: Mechanic = None, discount: DiscountStrategy = None):
        self.order_id = order_id
        self.car = car
        self.mechanic = mechanic
        self.status = "new"
        self.items = []
        self.discount = discount if discount is not None else NoDiscount()

    def assign_mechanic(self, mechanic: Mechanic):
        if self.status == "completed":
            raise InvalidStatusError("Нельзя менять механика в завершённом заказе!")
        self.mechanic = mechanic

    def add_item(self, item: OrderItem):
        if self.status == "completed":
            raise InvalidStatusError("Нельзя добавлять услуги в завершённый заказ!")
        self.items.append(item)

    def add_service(self, service: Service, quantity: int = 1):
        if self.status == "completed":
            raise InvalidStatusError("Нельзя добавлять услуги в завершённый заказ!")
        item = OrderItem(service, quantity=quantity)
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

    def calculate_raw_total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)

    def calculate_total(self) -> float:
        raw_total = self.calculate_raw_total()
        discount_amount = self.discount.calculate(raw_total)
        return raw_total - discount_amount

    def __str__(self):
        mech_str = self.mechanic.name if self.mechanic else "Не назначен"
        return f"Заказ №{self.order_id} [{self.status}] | Авто: {self.car.make} {self.car.model} | Механик: {mech_str} | Сумма: {self.calculate_raw_total()} руб. | К оплате: {self.calculate_total()} руб."