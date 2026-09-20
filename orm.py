from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, ClassVar, Iterable, Mapping

import psycopg
from psycopg import sql


class Field:
    def __init__(self, python_type: type | tuple[type, ...], primary_key: bool = False, nullable: bool = False):
        self.python_type = python_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            return self
        return instance.__dict__.get(self.name)

    def __set__(self, instance: Any, value: Any) -> None:
        if value is None:
            if not self.nullable and not self.primary_key:
                raise ValueError(f"{self.name} cannot be None")
        elif not isinstance(value, self.python_type):
            raise TypeError(f"{self.name} must be {self.python_type}")
        instance.__dict__[self.name] = value


class IntegerField(Field):
    def __init__(self, primary_key: bool = False, nullable: bool = False):
        super().__init__(int, primary_key=primary_key, nullable=nullable)


class StringField(Field):
    def __init__(self, nullable: bool = False):
        super().__init__(str, nullable=nullable)


class DateTimeField(Field):
    def __init__(self, nullable: bool = False):
        super().__init__((datetime, date), nullable=nullable)


class DecimalField(Field):
    def __init__(self, nullable: bool = False):
        super().__init__((Decimal, int, float), nullable=nullable)


class ForeignKey(IntegerField):
    def __init__(self, target: type[Model] | str, nullable: bool = False):
        super().__init__(nullable=nullable)
        self.target = target


@dataclass(frozen=True)
class ModelMetadata:
    table_name: str
    primary_key: Field
    fields: tuple[Field, ...]

    @property
    def columns(self) -> tuple[Field, ...]:
        return (self.primary_key, *self.fields)

    def field(self, name: str) -> Field:
        for field in self.columns:
            if field.name == name:
                return field
        raise ValueError(f"Unknown field: {name}")


class OneToMany:
    def __init__(self, target: type[Model], foreign_key: str):
        self.target = target
        self.foreign_key = foreign_key

    def __get__(self, instance: Model | None, owner: type | None = None) -> OneToManyManager | OneToMany:
        if instance is None:
            return self
        return OneToManyManager(instance, self.target, self.foreign_key)


class OneToManyManager:
    def __init__(self, owner: Model, target: type[Model], foreign_key: str):
        self.owner = owner
        self.target = target
        self.foreign_key = foreign_key

    def all(self) -> list[Model]:
        owner_id = getattr(self.owner, self.owner._meta.primary_key.name)
        if owner_id is None:
            return []
        return self.target.filter(**{self.foreign_key: owner_id})


class ManyToMany:
    def __init__(self, target: type[Model], through: type[Model], source_field: str, target_field: str):
        self.target = target
        self.through = through
        self.source_field = source_field
        self.target_field = target_field

    def __get__(self, instance: Model | None, owner: type | None = None) -> ManyToManyManager | ManyToMany:
        if instance is None:
            return self
        return ManyToManyManager(instance, self.target, self.through, self.source_field, self.target_field)


class ManyToManyManager:
    def __init__(
        self,
        owner: Model,
        target: type[Model],
        through: type[Model],
        source_field: str,
        target_field: str,
    ):
        self.owner = owner
        self.target = target
        self.through = through
        self.source_field = source_field
        self.target_field = target_field

    def all(self) -> list[Model]:
        owner_id = getattr(self.owner, self.owner._meta.primary_key.name)
        if owner_id is None:
            return []
        links = self.through.filter(**{self.source_field: owner_id})
        result = []
        for link in links:
            item = self.target.get(getattr(link, self.target_field))
            if item is not None:
                result.append(item)
        return result

    def add(self, target: Model, **through_values: Any) -> Model:
        owner_id = getattr(self.owner, self.owner._meta.primary_key.name)
        target_id = getattr(target, target._meta.primary_key.name)
        if owner_id is None or target_id is None:
            raise ValueError("Both related objects must be saved before creating a relation")
        values = {
            self.source_field: owner_id,
            self.target_field: target_id,
            **through_values,
        }
        return self.through(**values).save()


class Model:
    _connection: ClassVar[psycopg.Connection | None] = None
    _transaction_depth: ClassVar[int] = 0
    _meta: ClassVar[ModelMetadata]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        declared = tuple(value for value in cls.__dict__.values() if isinstance(value, Field))
        primary_keys = tuple(field for field in declared if field.primary_key)
        if len(primary_keys) != 1:
            raise TypeError(f"{cls.__name__} must declare exactly one primary key")
        meta_class = getattr(cls, "Meta", None)
        table_name = getattr(meta_class, "table_name", f"{cls.__name__.lower()}s")
        cls._meta = ModelMetadata(
            table_name=table_name,
            primary_key=primary_keys[0],
            fields=tuple(field for field in declared if not field.primary_key),
        )

    @classmethod
    def set_connection(cls, connection: psycopg.Connection) -> None:
        Model._connection = connection

    @classmethod
    def _get_connection(cls) -> psycopg.Connection:
        if Model._connection is None:
            raise RuntimeError("Database connection is not configured")
        return Model._connection

    @classmethod
    def _identifiers(cls, fields: Iterable[Field]) -> sql.Composed:
        return sql.SQL(", ").join(sql.Identifier(field.name) for field in fields)

    @classmethod
    def _select_query(cls, where: sql.Composed | None = None) -> sql.Composed:
        query = sql.SQL("SELECT {columns} FROM {table}").format(
            columns=cls._identifiers(cls._meta.columns),
            table=sql.Identifier(cls._meta.table_name),
        )
        if where is not None:
            query += sql.SQL(" WHERE ") + where
        return query

    def _values(self) -> tuple[Any, ...]:
        return tuple(getattr(self, field.name) for field in self._meta.fields)

    @classmethod
    def _commit_if_needed(cls) -> None:
        if Model._transaction_depth == 0:
            cls._get_connection().commit()

    @classmethod
    @contextmanager
    def transaction(cls):
        connection = cls._get_connection()
        outermost = Model._transaction_depth == 0
        Model._transaction_depth += 1
        try:
            yield
        except Exception:
            if outermost:
                connection.rollback()
            raise
        else:
            if outermost:
                connection.commit()
        finally:
            Model._transaction_depth -= 1

    def save(self) -> Model:
        cls = type(self)
        connection = cls._get_connection()
        entity_id = getattr(self, cls._meta.primary_key.name)
        with connection.cursor() as cursor:
            if entity_id is None:
                query = sql.SQL(
                    "INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING {primary_key}"
                ).format(
                    table=sql.Identifier(cls._meta.table_name),
                    columns=cls._identifiers(cls._meta.fields),
                    placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in cls._meta.fields),
                    primary_key=sql.Identifier(cls._meta.primary_key.name),
                )
                cursor.execute(query, self._values())
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("INSERT did not return a primary key")
                setattr(self, cls._meta.primary_key.name, row[0])
            else:
                assignments = sql.SQL(", ").join(
                    sql.SQL("{column} = %s").format(column=sql.Identifier(field.name))
                    for field in cls._meta.fields
                )
                query = sql.SQL("UPDATE {table} SET {assignments} WHERE {primary_key} = %s").format(
                    table=sql.Identifier(cls._meta.table_name),
                    assignments=assignments,
                    primary_key=sql.Identifier(cls._meta.primary_key.name),
                )
                cursor.execute(query, (*self._values(), entity_id))
        cls._commit_if_needed()
        return self

    def delete(self) -> bool:
        cls = type(self)
        entity_id = getattr(self, cls._meta.primary_key.name)
        if entity_id is None:
            return False
        query = sql.SQL("DELETE FROM {table} WHERE {primary_key} = %s").format(
            table=sql.Identifier(cls._meta.table_name),
            primary_key=sql.Identifier(cls._meta.primary_key.name),
        )
        with cls._get_connection().cursor() as cursor:
            cursor.execute(query, (entity_id,))
            deleted = cursor.rowcount > 0
        cls._commit_if_needed()
        if deleted:
            setattr(self, cls._meta.primary_key.name, None)
        return deleted

    @classmethod
    def get(cls, entity_id: Any) -> Model | None:
        condition = sql.SQL("{column} = %s").format(column=sql.Identifier(cls._meta.primary_key.name))
        with cls._get_connection().cursor() as cursor:
            cursor.execute(cls._select_query(condition), (entity_id,))
            row = cursor.fetchone()
            return None if row is None else cls._from_row(row, cursor.description)

    @classmethod
    def all(cls) -> list[Model]:
        with cls._get_connection().cursor() as cursor:
            cursor.execute(cls._select_query())
            return [cls._from_row(row, cursor.description) for row in cursor.fetchall()]

    @classmethod
    def filter(cls, **conditions: Any) -> list[Model]:
        if not conditions:
            return cls.all()
        predicates = []
        values = []
        for expression, value in conditions.items():
            field_name, separator, lookup = expression.partition("__")
            field = cls._meta.field(field_name)
            if separator and lookup != "greater_than":
                raise ValueError(f"Unsupported lookup: {lookup}")
            operator = ">" if lookup == "greater_than" else "="
            predicates.append(
                sql.SQL("{column} " + operator + " %s").format(column=sql.Identifier(field.name))
            )
            values.append(value)
        where = sql.SQL(" AND ").join(predicates)
        with cls._get_connection().cursor() as cursor:
            cursor.execute(cls._select_query(where), tuple(values))
            return [cls._from_row(row, cursor.description) for row in cursor.fetchall()]

    @classmethod
    def _from_row(cls, row: Any, description: Any = None) -> Model:
        if isinstance(row, Mapping):
            values = dict(row)
        else:
            if description is None:
                raise ValueError("Cursor description is required for tuple rows")
            values = {
                column.name if hasattr(column, "name") else column[0]: value
                for column, value in zip(description, row)
            }
        obj = cls.__new__(cls)
        for field in cls._meta.columns:
            if field.name in values:
                setattr(obj, field.name, values[field.name])
        return obj
