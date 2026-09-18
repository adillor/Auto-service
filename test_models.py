import pytest # noqa: F401
from models import (
    Client, Car, Mechanic, Service, ServiceOrder,
    PercentageDiscount, ThresholdDiscount, FixedDiscount,
    InvalidStatusError, OrderValidationError, DomainError
)

def test_full_order_lifecycle():
    client = Client("Адиль", "+7777")
    car = Car("Toyota", "Camry", "VIN1", owner=client)
    mechanic = Mechanic("Алексей", "Моторист")
    service = Service("Замена масла", 2000.0)

    order = ServiceOrder(order_id=1, car=car, mechanic=mechanic)
    order.add_service(service)

    assert order.status == "new"
    order.start_order()
    assert order.status == "in_progress"
    order.complete_order()
    assert order.status == "completed"

def test_car_reassignment_between_clients():
    client1 = Client("Иван", "+7111")
    client2 = Client("Олег", "+7222")
    car = Car("BMW", "X5", "VIN2", owner=client1)

    assert car in client1.cars
    client2.add_car(car)

    assert car not in client1.cars
    assert car in client2.cars
    assert car.owner == client2

def test_order_discounts():
    service = Service("Ремонт", 10000.0)
    car = Car("Audi", "A6", "VIN3")

    order_percent = ServiceOrder(1, car, discount=PercentageDiscount(10))
    order_percent.add_service(service)
    assert order_percent.calculate_total() == 9000.0

    order_threshold_active = ServiceOrder(2, car, discount=ThresholdDiscount(5000, 20))
    order_threshold_active.add_service(service)
    assert order_threshold_active.calculate_total() == 8000.0

    order_threshold_inactive = ServiceOrder(3, car, discount=ThresholdDiscount(15000, 20))
    order_threshold_inactive.add_service(service)
    assert order_threshold_inactive.calculate_total() == 10000.0

def test_cannot_start_order_without_mechanic():
    car = Car("Honda", "Civic", "VIN4")
    order = ServiceOrder(1, car)
    order.add_service(Service("Диагностика", 1000.0))

    with pytest.raises(OrderValidationError):
        order.start_order()

def test_cannot_start_empty_order():
    car = Car("Honda", "Civic", "VIN5")
    mechanic = Mechanic("Петр", "Электрик")
    order = ServiceOrder(1, car, mechanic=mechanic)

    with pytest.raises(OrderValidationError):
        order.start_order()

def test_cannot_modify_completed_order():
    car = Car("Kia", "Rio", "VIN6")
    mechanic = Mechanic("Сергей", "Маляр")
    service = Service("Покраска", 5000.0)

    order = ServiceOrder(1, car, mechanic=mechanic)
    order.add_service(service)
    order.start_order()
    order.complete_order()

    with pytest.raises(InvalidStatusError):
        order.add_service(service)

    with pytest.raises(InvalidStatusError):
        order.assign_mechanic(mechanic)

def test_invalid_discount_parameters():
    with pytest.raises(DomainError):
        PercentageDiscount(150)

    with pytest.raises(DomainError):
        FixedDiscount(-500)