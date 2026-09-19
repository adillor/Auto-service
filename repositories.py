from abc import ABC, abstractmethod
import psycopg
from models import (
    Client, Car, Mechanic, Service, ServiceOrder,
    NoDiscount, PercentageDiscount, FixedDiscount, ThresholdDiscount
)

class AbstractRepository(ABC):
    @abstractmethod
    def add(self, entity):
        pass

    @abstractmethod
    def get_by_id(self, entity_id):
        pass

    @abstractmethod
    def get_all(self):
        pass


class ClientRepository(AbstractRepository):
    def __init__(self, conn):
        self.conn = conn

    def add(self, client: Client) -> Client:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO clients (name, phone) VALUES (%s, %s) RETURNING id;",
                (client.name, client.phone)
            )
            client_id = cur.fetchone()[0]
            self.conn.commit()
            return self.get_by_id(client_id)

    def get_by_id(self, client_id: int) -> Client | None:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, phone FROM clients WHERE id = %s;", (client_id,))
            row = cur.fetchone()
            if not row:
                return None
            client = Client(row[1], row[2])
            client.id = row[0]
            
            cur.execute("SELECT id, make, model, vin FROM cars WHERE owner_id = %s;", (client_id,))
            car_rows = cur.fetchall()
            for cr in car_rows:
                car = Car(cr[1], cr[2], cr[3], owner=client)
                car.id = cr[0]
            return client

    def get_all(self) -> list[Client]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM clients;")
            rows = cur.fetchall()
            return [self.get_by_id(row[0]) for row in rows]


class CarRepository(AbstractRepository):
    def __init__(self, conn):
        self.conn = conn

    def add(self, car: Car) -> Car:
        with self.conn.cursor() as cur:
            owner_id = getattr(car.owner, 'id', None) if car.owner else None
            cur.execute(
                "INSERT INTO cars (make, model, vin, owner_id) VALUES (%s, %s, %s, %s) RETURNING id;",
                (car.make, car.model, car.vin, owner_id)
            )
            car_id = cur.fetchone()[0]
            car.id = car_id
            self.conn.commit()
            return car

    def get_by_id(self, car_id: int) -> Car | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.make, c.model, c.vin, cl.id, cl.name, cl.phone
                FROM cars c
                LEFT JOIN clients cl ON c.owner_id = cl.id
                WHERE c.id = %s;
                """,
                (car_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            
            owner = None
            if row[4]:
                owner = Client(row[5], row[6])
                owner.id = row[4]
                
            car = Car(row[1], row[2], row[3], owner=owner)
            car.id = row[0]
            return car

    def get_all(self) -> list[Car]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM cars;")
            rows = cur.fetchall()
            return [self.get_by_id(row[0]) for row in rows]


class ServiceOrderRepository(AbstractRepository):
    def __init__(self, conn):
        self.conn = conn

    def add(self, order: ServiceOrder) -> ServiceOrder:
        with self.conn.transaction():
            with self.conn.cursor() as cur:
                disc_type = 'none'
                val1, val2 = 0, 0
                if isinstance(order.discount, PercentageDiscount):
                    disc_type, val1 = 'percentage', order.discount.percent
                elif isinstance(order.discount, FixedDiscount):
                    disc_type, val1 = 'fixed', order.discount.amount
                elif isinstance(order.discount, ThresholdDiscount):
                    disc_type, val1, val2 = 'threshold', order.discount.threshold, order.discount.percent

                car_id = getattr(order.car, 'id', None)
                mechanic_id = getattr(order.mechanic, 'id', None)

                cur.execute(
                    """
                    INSERT INTO service_orders 
                    (car_id, mechanic_id, status, discount_type, discount_val1, discount_val2)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
                    """,
                    (car_id, mechanic_id, order.status, disc_type, val1, val2)
                )
                order_id = cur.fetchone()[0]
                order.order_id = order_id

                for item in order.items:
                    service_id = getattr(item.service, 'id', None)
                    cur.execute(
                        "INSERT INTO order_items (order_id, service_id, price) VALUES (%s, %s, %s);",
                        (order_id, service_id, item.price)
                    )
        return self.get_by_id(order.order_id)

    def get_by_id(self, order_id: int) -> ServiceOrder | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT so.id, so.status, so.discount_type, so.discount_val1, so.discount_val2,
                       c.id, c.make, c.model, c.vin,
                       m.id, m.name, m.specialization
                FROM service_orders so
                JOIN cars c ON so.car_id = c.id
                LEFT JOIN mechanics m ON so.mechanic_id = m.id
                WHERE so.id = %s;
                """,
                (order_id,)
            )
            row = cur.fetchone()
            if not row:
                return None

            car = Car(row[6], row[7], row[8])
            car.id = row[5]

            mechanic = None
            if row[9]:
                mechanic = Mechanic(row[10], row[11])
                mechanic.id = row[9]

            disc_type, val1, val2 = row[2], float(row[3]), float(row[4])
            if disc_type == 'percentage':
                discount = PercentageDiscount(val1)
            elif disc_type == 'fixed':
                discount = FixedDiscount(val1)
            elif disc_type == 'threshold':
                discount = ThresholdDiscount(val1, val2)
            else:
                discount = NoDiscount()

            order = ServiceOrder(order_id=row[0], car=car, mechanic=mechanic, discount=discount)
            order.status = row[1]

            cur.execute(
                """
                SELECT s.id, s.title, oi.price 
                FROM order_items oi
                JOIN services s ON oi.service_id = s.id
                WHERE oi.order_id = %s;
                """,
                (order_id,)
            )
            for item_row in cur.fetchall():
                srv = Service(item_row[1], float(item_row[2]))
                srv.id = item_row[0]
                order.add_service(srv)

            return order

    def get_all(self) -> list[ServiceOrder]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM service_orders;")
            rows = cur.fetchall()
            return [self.get_by_id(row[0]) for row in rows]