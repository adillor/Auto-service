from abc import ABC, abstractmethod
import psycopg
from models import Client, Car, ServiceOrder  # Импортируем все сущности


# --- 1. БАЗОВЫЕ КЛАССЫ (Инфраструктура) ---

class EntityMapper(ABC):
    """Интерфейс, сообщающий persistence-механизму сведения о классе."""
    table_name: str
    primary_key: str = "id"
    fields: list[str]

    @abstractmethod
    def to_dict(self, entity) -> dict:
        """Преобразует объект в словарь для INSERT / UPDATE."""
        pass

    @abstractmethod
    def to_entity(self, row: tuple, cur_description) -> object:
        """Преобразует кортеж из БД обратно в объект доменной модели."""
        pass


class BaseRepository:
    """Универсальный репозиторий, реализующий общий CRUD-код."""
    def __init__(self, conn: psycopg.Connection, mapper: EntityMapper):
        self.conn = conn
        self.mapper = mapper

    def _execute(self, query: str, params: tuple = (), fetch_one=False, fetch_all=False):
        """Единый механизм выполнения запросов."""
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            if fetch_one:
                return cur.fetchone(), cur.description
            if fetch_all:
                return cur.fetchall(), cur.description
            self.conn.commit()
            return None

    def add(self, entity):
        data = self.mapper.to_dict(entity)
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        
        query = f"""
            INSERT INTO {self.mapper.table_name} ({columns}) 
            VALUES ({placeholders}) 
            RETURNING {self.mapper.primary_key};
        """
        row, _ = self._execute(query, tuple(data.values()), fetch_one=True)
        setattr(entity, self.mapper.primary_key, row[0])
        return entity

    def get_by_id(self, entity_id: int):
        query = f"SELECT * FROM {self.mapper.table_name} WHERE {self.mapper.primary_key} = %s;"
        row, desc = self._execute(query, (entity_id,), fetch_one=True)
        if not row:
            return None
        return self.mapper.to_entity(row, desc)

    def get_all(self) -> list:
        query = f"SELECT * FROM {self.mapper.table_name};"
        rows, desc = self._execute(query, fetch_all=True)
        return [self.mapper.to_entity(r, desc) for r in rows]

    def update(self, entity) -> bool:
        """Операция обновления (Требование PR-07)."""
        data = self.mapper.to_dict(entity)
        entity_id = getattr(entity, self.mapper.primary_key)
        set_clause = ", ".join([f"{col} = %s" for col in data.keys()])
        
        query = f"""
            UPDATE {self.mapper.table_name} 
            SET {set_clause} 
            WHERE {self.mapper.primary_key} = %s;
        """
        params = tuple(data.values()) + (entity_id,)
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            self.conn.commit()
            return cur.rowcount > 0

    def delete(self, entity_id: int) -> bool:
        """Операция удаления (Требование PR-07)."""
        query = f"DELETE FROM {self.mapper.table_name} WHERE {self.mapper.primary_key} = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (entity_id,))
            self.conn.commit()
            return cur.rowcount > 0


# --- 2. CLIENT REPOSITORY ---

class ClientMapper(EntityMapper):
    table_name = "clients"
    primary_key = "id"
    fields = ["name", "phone"]

    def to_dict(self, client: Client) -> dict:
        return {"name": client.name, "phone": client.phone}

    def to_entity(self, row: tuple, cur_description) -> Client:
        col_names = [desc[0] for desc in cur_description]
        data = dict(zip(col_names, row))
        
        client = Client(data["name"], data["phone"])
        client.id = data["id"]
        return client


class ClientRepository(BaseRepository):
    def __init__(self, conn: psycopg.Connection):
        super().__init__(conn, ClientMapper())


# --- 3. CAR REPOSITORY ---

class CarMapper(EntityMapper):
    table_name = "cars"
    primary_key = "id"
    fields = ["vin", "model", "client_id"]

    def to_dict(self, car: Car) -> dict:
        return {
            "vin": car.vin,
            "model": car.model,
            "client_id": car.client_id if hasattr(car, "client_id") else None
        }

    def to_entity(self, row: tuple, cur_description) -> Car:
        col_names = [desc[0] for desc in cur_description]
        data = dict(zip(col_names, row))
        
        car = Car(data["model"], data["vin"])
        car.id = data["id"]
        if "client_id" in data:
            car.client_id = data["client_id"]
        return car


class CarRepository(BaseRepository):
    def __init__(self, conn: psycopg.Connection):
        super().__init__(conn, CarMapper())


# --- 4. SERVICE ORDER REPOSITORY ---

class ServiceOrderMapper(EntityMapper):
    table_name = "service_orders"
    primary_key = "id"
    fields = ["car_id", "mechanic", "status"]

    def to_dict(self, order: ServiceOrder) -> dict:
        return {
            "car_id": getattr(order, "car_id", None),
            "mechanic": order.mechanic,
            "status": order.status
        }

    def to_entity(self, row: tuple, cur_description) -> ServiceOrder:
        col_names = [desc[0] for desc in cur_description]
        data = dict(zip(col_names, row))
        
        # Передаем None вместо объекта Car, если загрузка происходила без JOIN
        order = ServiceOrder(car=None, mechanic=data["mechanic"])
        order.id = data["id"]
        order.status = data["status"]
        if "car_id" in data:
            order.car_id = data["car_id"]
        return order


class ServiceOrderRepository(BaseRepository):
    def __init__(self, conn: psycopg.Connection):
        super().__init__(conn, ServiceOrderMapper())