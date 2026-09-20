from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Iterable, Mapping

import psycopg
from psycopg import sql


@dataclass(frozen=True)
class ModelMetadata:
    """Database mapping shared by all operations of one model class."""

    table_name: str
    primary_key: str
    fields: tuple[str, ...]

    @property
    def columns(self) -> tuple[str, ...]:
        """Columns returned when an object is read from the database."""
        return (self.primary_key, *self.fields)


class Model:
    """Base class for persisted objects.

    A subclass declares persisted properties as annotations and may override
    its table name in ``Meta``. For example::

        class Client(Model):
            id: int | None
            name: str
            phone: str

            class Meta:
                table_name = "clients"
    """

    _connection: ClassVar[psycopg.Connection | None] = None
    _meta: ClassVar[ModelMetadata]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Collect model metadata once, when a subclass is declared."""
        super().__init_subclass__(**kwargs)

        meta_class = getattr(cls, "Meta", None)
        table_name = getattr(meta_class, "table_name", f"{cls.__name__.lower()}s")
        primary_key = getattr(meta_class, "primary_key", "id")

        annotations = cls.__dict__.get("__annotations__", {})
        fields = tuple(name for name in annotations if name != primary_key and not name.startswith("_"))
        if not fields:
            raise TypeError(
                f"{cls.__name__} must declare at least one persisted field with type annotations."
            )

        cls._meta = ModelMetadata(
            table_name=table_name,
            primary_key=primary_key,
            fields=fields,
        )

        cls.table_name = table_name
        cls.primary_key = primary_key
        cls.fields = list(fields)

    @classmethod
    def set_connection(cls, connection: psycopg.Connection) -> None:
        """Set the PostgreSQL connection used by every model subclass."""
        Model._connection = connection

    @classmethod
    def _get_connection(cls) -> psycopg.Connection:
        if Model._connection is None:
            raise RuntimeError("Database connection is not configured. Call Model.set_connection(conn).")
        return Model._connection

    @classmethod
    def _identifiers(cls, names: Iterable[str]) -> sql.Composed:
        return sql.SQL(", ").join(sql.Identifier(name) for name in names)

    @classmethod
    def _select_query(cls, where: bool = False) -> sql.Composed:
        query = sql.SQL("SELECT {columns} FROM {table}").format(
            columns=cls._identifiers(cls._meta.columns),
            table=sql.Identifier(cls._meta.table_name),
        )
        if where:
            query += sql.SQL(" WHERE {primary_key} = %s").format(
                primary_key=sql.Identifier(cls._meta.primary_key)
            )
        return query

    def _values(self) -> tuple[Any, ...]:
        """Read only declared persistent fields, never helper attributes."""
        return tuple(getattr(self, field) for field in self._meta.fields)

    def save(self) -> "Model":
        """Insert a new object or update an object that already has a primary key."""
        cls = type(self)
        connection = cls._get_connection()
        entity_id = getattr(self, cls._meta.primary_key, None)

        with connection.cursor() as cursor:
            if entity_id is None:
                query = sql.SQL(
                    "INSERT INTO {table} ({columns}) VALUES ({placeholders}) "
                    "RETURNING {primary_key}"
                ).format(
                    table=sql.Identifier(cls._meta.table_name),
                    columns=cls._identifiers(cls._meta.fields),
                    placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in cls._meta.fields),
                    primary_key=sql.Identifier(cls._meta.primary_key),
                )
                cursor.execute(query, self._values())
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("INSERT did not return a primary key.")
                setattr(self, cls._meta.primary_key, row[0])
            else:
                assignments = sql.SQL(", ").join(
                    sql.SQL("{column} = %s").format(column=sql.Identifier(field))
                    for field in cls._meta.fields
                )
                query = sql.SQL("UPDATE {table} SET {assignments} WHERE {primary_key} = %s").format(
                    table=sql.Identifier(cls._meta.table_name),
                    assignments=assignments,
                    primary_key=sql.Identifier(cls._meta.primary_key),
                )
                cursor.execute(query, (*self._values(), entity_id))

            connection.commit()
        return self

    def delete(self) -> bool:
        """Delete this object. Returns ``False`` for an unsaved object."""
        cls = type(self)
        entity_id = getattr(self, cls._meta.primary_key, None)
        if entity_id is None:
            return False

        query = sql.SQL("DELETE FROM {table} WHERE {primary_key} = %s").format(
            table=sql.Identifier(cls._meta.table_name),
            primary_key=sql.Identifier(cls._meta.primary_key),
        )
        connection = cls._get_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, (entity_id,))
            deleted = cursor.rowcount > 0
            connection.commit()

        if deleted:
            setattr(self, cls._meta.primary_key, None)
        return deleted

    @classmethod
    def get(cls, entity_id: Any) -> "Model | None":
        """Return one model instance by primary key, or ``None`` if it is absent."""
        with cls._get_connection().cursor() as cursor:
            cursor.execute(cls._select_query(where=True), (entity_id,))
            row = cursor.fetchone()
            return None if row is None else cls._from_row(row, cursor.description)

    @classmethod
    def all(cls) -> list["Model"]:
        """Return all rows from the model's table as model instances."""
        with cls._get_connection().cursor() as cursor:
            cursor.execute(cls._select_query())
            return [cls._from_row(row, cursor.description) for row in cursor.fetchall()]

    @classmethod
    def _from_row(cls, row: Any, description: Any = None) -> "Model":
        """Create an object from either psycopg tuple or dictionary rows."""
        if isinstance(row, Mapping):
            values = dict(row)
        else:
            if description is None:
                raise ValueError("Cursor description is required for tuple rows.")
            values = {
                column.name if hasattr(column, "name") else column[0]: value
                for column, value in zip(description, row)
            }

        obj = cls.__new__(cls)
        for column in cls._meta.columns:
            if column in values:
                setattr(obj, column, values[column])
        return obj
