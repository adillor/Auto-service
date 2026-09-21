# AutoService — PR-10

Persistence-слой перенесён с собственной ORM PR-09 на SQLAlchemy 2.x и
PostgreSQL. Предметные сущности сохранены: клиент, автомобиль, механик,
услуга, заказ и позиция заказа.

## Запуск

```text
pip install -r requirements.txt
python main.py
pytest -q
```

Подключение к PostgreSQL задаётся в `database.py`. Схема базы описана в
`schema.sql`; для базы из PR-08 используйте `migration_pr09.sql`.

## SQLAlchemy API

Модели описаны декларативно через `Mapped`, `mapped_column` и `relationship`.
CRUD выполняется через `Session.add`, `Session.get`, изменение атрибутов и
`Session.delete`. Выборки используют `select`.

```python
orders = session.scalars(
    select(ServiceOrder).where(
        ServiceOrder.status == "new",
        ServiceOrder.created_at > started_at,
    )
).all()
```

`Client.cars` реализует связь `1:N`. Заказ и услуги связаны `M:N` через
объект `OrderItem`, который дополнительно хранит цену услуги в заказе.
`ServiceOrder.create_with_services` создаёт заказ и позиции, а сценарий
оборачивает составную операцию в `with SessionLocal.begin()`.

## Сравнение ORM

| Возможность | Собственная ORM PR-09 | SQLAlchemy 2.x PR-10 |
| --- | --- | --- |
| Mapping | `Field`, `ForeignKey`, метаданные вручную | `Mapped`, `mapped_column`, декларативный mapping |
| CRUD | `save`, `get`, `filter`, `delete` | `Session.add`, `Session.get`, `select`, `Session.delete` |
| Связи | Самописные `OneToMany` и `ManyToMany` | `relationship`, association object и association proxy |
| Транзакции | Собственный контекст `Model.transaction()` | `Session.begin()` и rollback Session |
| Удобство | Небольшой API, понятный для учебного проекта | Готовый Unit of Work, identity map, загрузка связей и богатые запросы |
| Ограничения | Нет JOIN, миграций, lazy loading и сложных запросов | Больше API и настроек, требуется изучение Session и жизненного цикла объектов |

Собственная ORM сохранена в `orm.py` как результат PR-09 и материал для
сравнения, но прикладной сценарий PR-10 её не использует.
