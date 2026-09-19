import psycopg
from models import Client
from repositories import ClientRepository

DB_PARAMS = "dbname=autoservice user=postgres password=postgres host=localhost port=5432"

def run_demo():
    with psycopg.connect(DB_PARAMS) as conn:
        repo = ClientRepository(conn)

        client = Client("Сергей Петров", "+79001112233")
        client = repo.add(client)
        print(f"[ADD] Создан клиент ID={client.id}: {client.name}")

        client.name = "Сергей Сергеев"
        repo.update(client)
        updated_client = repo.get_by_id(client.id)
        print(f"[UPDATE] Обновлён клиент ID={updated_client.id}: {updated_client.name}")

        repo.delete(client.id)
        deleted_client = repo.get_by_id(client.id)
        print(f"[DELETE] Клиент найден после удаления? {deleted_client is not None}")

if __name__ == "__main__":
    run_demo()