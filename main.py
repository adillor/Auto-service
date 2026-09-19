import psycopg
from models import Client, Car, Mechanic, Service, ServiceOrder, PercentageDiscount
from repositories import ClientRepository, CarRepository, ServiceOrderRepository

DB_PARAMS = "dbname=autoservice user=postgres password=postgres host=localhost port=5432"

def init_db(conn):
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()
    with conn.cursor() as cur:
        cur.execute(schema)
    conn.commit()

def run_demo():
    with psycopg.connect(DB_PARAMS) as conn:
        init_db(conn)

        client_repo = ClientRepository(conn)
        car_repo = CarRepository(conn)
        order_repo = ServiceOrderRepository(conn)

        client = Client("Иван Иванов", "+79990001122")
        client = client_repo.add(client)

        car = Car("Toyota", "Camry", "VIN123456", owner=client)
        car = car_repo.add(car)

        with conn.cursor() as cur:
            cur.execute("INSERT INTO mechanics (name, specialization) VALUES (%s, %s) RETURNING id;", ("Алексей", "Моторист"))
            mech_id = cur.fetchone()[0]
            cur.execute("INSERT INTO services (title, price) VALUES (%s, %s) RETURNING id;", ("Диагностика", 3000.0))
            srv_id = cur.fetchone()[0]
            conn.commit()

        mechanic = Mechanic("Алексей", "Моторист")
        mechanic.id = mech_id
        service = Service("Диагностика", 3000.0)
        service.id = srv_id

        order = ServiceOrder(order_id=0, car=car, mechanic=mechanic, discount=PercentageDiscount(10))
        order.add_service(service)
        order.start_order()

        saved_order = order_repo.add(order)
        order_id = saved_order.order_id
        print(f"[СОХРАНЕНО] Заказ №{order_id} со статусом '{saved_order.status}' сохранён в PostgreSQL.")

    print("\n--- Перезапуск программы и чтение из БД ---")

    with psycopg.connect(DB_PARAMS) as conn:
        order_repo = ServiceOrderRepository(conn)
        client_repo = ClientRepository(conn)

        restored_order = order_repo.get_by_id(order_id)
        restored_client = client_repo.get_by_id(client.id)

        print(f"[ВОССТАНОВЛЕНО] Заказ №{restored_order.order_id}:")
        print(f"  Автомобиль: {restored_order.car.make} {restored_order.car.model} (VIN: {restored_order.car.vin})")
        print(f"  Механик: {restored_order.mechanic.name}")
        print(f"  Статус: {restored_order.status}")
        print(f"  Итоговая стоимость с учётом скидки: {restored_order.calculate_total()} руб.")
        print(f"[ВОССТАНОВЛЕНО] Клиент: {restored_client.name}, Машин в гараже: {len(restored_client.cars)}")

if __name__ == "__main__":
    run_demo()