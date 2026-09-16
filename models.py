class Client:
    def __init__(self,name:str,phone:str):
        self.name = name
        self.phone = phone
    def __str__(self):
        return f"Клиент {self.name} телефон:{self.phone}"

class Car:
    def __init__(self,make: str,model:str,vin:str,owner:Client=None):
        self.make = make
        self.model = model
        self.vin = vin
        self.owner = owner
    def __str__(self):
        owner_name = self.owner.name if self.owner else "Нет владельца"
        return f"Авто: {self.make} {self.model} [{self.vin}] — Владелец: {owner_name}"

class Mechanic:
    def __init__(self,name:str,role:str):
        self.name = name
        self.role = role

    def __str__(self):
        return f"Механик: {self.name} (специализация: {self.role})"

class Service:
    def __init__(self,title:str,base_price:float):
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
    def __str__(self):
        mech_str = self.mechanic.name if self.mechanic else "Не назначен"
        return f"Заказ №{self.order_id} [{self.status}] | Авто: {self.car.make} {self.car.model} | Механик: {mech_str}"

#Простой сценарий запуска, демонстрирующий создание объектов.
if __name__ == "__main__":
    print("Демонстрация работы объектов AutoService")

    client1 = Client("adil", "+7-777-777-77-77")
    client2 = Client("ООО Adil", "+7-777-777-77-67")

    car1 = Car("Toyota", "Camry", "А123АА777", client1)
    car2 = Car("GAZ", "Gazelle", "В456ВВ777", client2)

    mechanic1 = Mechanic("Алексей", "Моторист")

    service1 = Service("Замена масла", 1500.0)
    service2 = Service("Диагностика двигателя", 2000.0)

    item1 = Order_item(service1, quantity=1)
    item2 = Order_item(service2, quantity=1)

    order1 = Service_order(order_id=1, car=car1, mechanic=mechanic1)
    order1.items.extend([item1, item2])

    print(client1)
    print(car1)
    print(mechanic1)
    print(service1)
    print(item1)
    print(order1)
        
