# AutoService API — PR-11

FastAPI добавляет REST API над предметной моделью и SQLAlchemy persistence-
слоем. HTTP-обработчики принимают запросы и вызывают `AutoServiceApplication`;
SQL и бизнес-правила в endpoints отсутствуют.

## Запуск

Сначала запустите PostgreSQL и создайте базу `autoservice`. Схема находится в
`schema.sql`.

```text
pip install -r requirements.txt
uvicorn api:app --reload
```

Откройте [Swagger UI](http://127.0.0.1:8000/docs) и выполните запросы через
браузер. Для запуска без автоматической перезагрузки используйте
`uvicorn api:app`.

## Основные endpoints

| Метод | URL | Назначение |
| --- | --- | --- |
| POST | `/clients` | Создать клиента |
| GET | `/clients/{id}` | Получить клиента |
| PATCH | `/clients/{id}` | Изменить клиента |
| POST | `/cars` | Создать автомобиль клиента |
| POST | `/services` | Создать услугу |
| POST | `/orders` | Создать заказ с услугами |
| GET | `/orders/{id}` | Получить заказ |
| PATCH | `/orders/{id}/status` | Перевести заказ в следующий статус |

Полный путь операции создания заказа: HTTP endpoint →
`AutoServiceApplication.create_order()` → `Session.begin()` → SQLAlchemy
models → PostgreSQL. Заказ и позиции `OrderItem` сохраняются одной
транзакцией.

## Ошибки

Pydantic возвращает `422` для некорректных входных данных. Прикладной слой
возвращает `404`, если объект не найден, и `400`, если нарушено правило
перехода статусов заказа. Бизнес-правило определено один раз в
`AutoServiceApplication`, а не повторяется в endpoint.

## Тесты

```text
pytest -q
```

`test_api.py` использует FastAPI `TestClient` и временную SQLite-базу для
интеграционной проверки API без изменения PostgreSQL.
