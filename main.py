import psycopg

from models import Car, Client
from orm import Model

DB_PARAMS = "dbname=autoservice user=postgres password=postgres host=127.0.0.1 port=5432 connect_timeout=5"


def run_demo() -> None:
    with psycopg.connect(DB_PARAMS) as connection:
        Model.set_connection(connection)

        client = Client("Сергей Петров", "+79001112233").save()
        client.phone = "+79001112234"
        client.save()

        car = Car("Toyota", "Camry", "VIN-001", owner_id=client.id).save()
        print(Client.get(client.id).name)
        print([item.model for item in Car.all()])

        car.delete()
        client.delete()


if __name__ == "__main__":
    run_demo()
