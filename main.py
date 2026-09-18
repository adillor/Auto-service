from models import Client, Car, Mechanic, Service, ServiceOrder, PercentageDiscount, ThresholdDiscount


def scenario_1_full_repair_cycle():
    client = Client("Адиль", "+7-700-111-22-33")
    car = Car("Toyota", "Camry", "VIN12345", owner=client)
    mechanic = Mechanic("Алексей", "Моторист")

    service_oil = Service("Замена масла", 1500.0)
    service_diag = Service("Компьютерная диагностика", 2500.0)

    order = ServiceOrder(order_id=101, car=car, discount=PercentageDiscount(10.0))
    order.assign_mechanic(mechanic)
    order.add_service(service_oil)
    order.add_service(service_diag)

    order.start_order()
    order.complete_order()

    print("--- Сценарий 1: Полный цикл обслуживания ---")
    print(order)


def scenario_2_car_ownership_transfer():
    seller = Client("Иван", "+7-700-000-00-01")
    buyer = Client("Алексей", "+7-700-000-00-02")
    car = Car("BMW", "X5", "VIN99999", owner=seller)

    buyer.add_car(car)

    print("\n--- Сценарий 2: Передача авто новому владельцу ---")
    print(f"Старый владелец (авто): {len(seller.cars)}")
    print(f"Новый владелец: {car.owner.name}")
    print(f"Машин у покупателя: {len(buyer.cars)}")


def scenario_3_threshold_discount_order():
    client = Client("Мария", "+7-700-333-44-55")
    car = Car("Hyundai", "Elantra", "VIN77777", owner=client)
    mechanic = Mechanic("Данияр", "Ходовик")

    service_brakes = Service("Замена колодок", 4000.0)
    discount = ThresholdDiscount(threshold=3000.0, percent=15.0)

    order = ServiceOrder(order_id=102, car=car, mechanic=mechanic, discount=discount)
    order.add_service(service_brakes)

    order.start_order()

    print("\n--- Сценарий 3: Расчет заказа с пороговой скидкой ---")
    print(order)


if __name__ == "__main__":
    scenario_1_full_repair_cycle()
    scenario_2_car_ownership_transfer()
    scenario_3_threshold_discount_order()