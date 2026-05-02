"""
Declarative model definitions for extension database tables.

Provides a lightweight, Django/SQLAlchemy-like way to declare extension
table schemas.  Models are **not** an ORM — they exist solely to generate
the JSON schema declaration that the Ask DIANA backend validates and applies.

Usage::

    from askdiana import ExtModel, StringField, IntegerField, DateTimeField

    class UserSettings(ExtModel):
        __tablename__ = "ext_myext_user_settings"

        user_id = StringField(primary_key=True, max_length=36)
        theme = StringField(max_length=50, nullable=True)
        font_size = IntegerField(nullable=True)
        updated_at = DateTimeField(nullable=True)

    # Generate the JSON schema dict
    schema = UserSettings.to_schema()

    # Or register + apply in one go
    UserSettings.setup(client, install_id, version="1.0.0")
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import AskDianaClient

# Registry of declared table names → model class (process-scoped, for duplicate detection)
_REGISTERED_TABLENAMES: Dict[str, type] = {}


# ------------------------------------------------------------------ #
# Field classes                                                        #
# ------------------------------------------------------------------ #


class Field:
    """Base field descriptor for ExtModel columns.

    Use the typed subclasses (``StringField``, ``IntegerField``, etc.)
    rather than this class directly.
    """

    field_type: str = ""

    def __init__(
        self,
        primary_key: bool = False,
        nullable: bool = True,
        max_length: Optional[int] = None,
    ):
        self.primary_key = primary_key
        self.nullable = nullable
        self.max_length = max_length
        self.name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def to_column_dict(self) -> Dict[str, Any]:
        """Return the column definition dict for the schema JSON."""
        col: Dict[str, Any] = {
            "name": self.name,
            "type": self.field_type,
        }
        if self.primary_key:
            col["primary_key"] = True
        if not self.nullable:
            col["nullable"] = False
        if self.max_length is not None:
            col["max_length"] = self.max_length
        return col


class StringField(Field):
    """VARCHAR column (``type: "string"``).

    Args:
        max_length: Maximum length (default 255).
        primary_key: Whether this column is (part of) the primary key.
        nullable: Whether the column allows NULL (default True).
    """

    field_type = "string"

    def __init__(self, max_length: int = 255, **kwargs: Any):
        super().__init__(max_length=max_length, **kwargs)


class TextField(Field):
    """TEXT column (``type: "text"``)."""

    field_type = "text"


class IntegerField(Field):
    """INT column (``type: "integer"``)."""

    field_type = "integer"


class FloatField(Field):
    """FLOAT column (``type: "float"``)."""

    field_type = "float"


class BooleanField(Field):
    """TINYINT(1) column (``type: "boolean"``)."""

    field_type = "boolean"


class DateTimeField(Field):
    """DATETIME column (``type: "datetime"``)."""

    field_type = "datetime"


class DateField(Field):
    """DATE column (``type: "date"``)."""

    field_type = "date"


class JsonField(Field):
    """JSON column (``type: "json"``)."""

    field_type = "json"


# ------------------------------------------------------------------ #
# Model metaclass & base class                                         #
# ------------------------------------------------------------------ #


class ExtModelMeta(type):
    """Metaclass that collects Field descriptors from the class body.

    Walks the MRO so that subclasses **inherit** parent fields.
    A child class can override a parent field by redefining it with
    the same attribute name.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple,
        namespace: dict,
    ) -> "ExtModelMeta":
        cls = super().__new__(mcs, name, bases, namespace)

        # Collect inherited fields from parent classes (furthest ancestor first)
        inherited: Dict[str, Field] = {}
        for base in reversed(cls.__mro__):
            if base is object:
                continue
            for attr_name, attr_value in vars(base).items():
                if isinstance(attr_value, Field):
                    inherited[attr_name] = attr_value

        # Override / add fields defined in this class body
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, Field):
                inherited[attr_name] = attr_value

        cls._fields = list(inherited.values())  # type: ignore[attr-defined]

        # Detect duplicate __tablename__ across model classes
        tablename = namespace.get("__tablename__", "")
        if tablename and tablename.startswith("ext_"):
            existing = _REGISTERED_TABLENAMES.get(tablename)
            if existing is not None and existing is not cls:
                raise ValueError(
                    f"Duplicate __tablename__ '{tablename}': already declared by "
                    f"'{existing.__name__}'. Each table name must be unique."
                )
            _REGISTERED_TABLENAMES[tablename] = cls

        return cls


class ExtModel(metaclass=ExtModelMeta):
    """Base class for extension table declarations.

    Subclass this and set ``__tablename__`` (must start with ``ext_``).
    Define columns using field descriptors.

    Example::

        class SyncHistory(ExtModel):
            __tablename__ = "ext_gdrive_sync_history"

            id = StringField(primary_key=True, max_length=36)
            install_id = StringField(max_length=36, nullable=False)
            file_name = StringField(max_length=500, nullable=False)
            status = StringField(max_length=50, nullable=False)
            synced_at = DateTimeField(nullable=True)
            metadata = JsonField(nullable=True)
    """

    __tablename__: str = ""
    _fields: List[Field] = []

    @classmethod
    def to_schema(cls) -> Dict[str, Any]:
        """Generate the schema declaration dict for ``register_schema()``.

        Returns::

            {
                "tables": [
                    {
                        "name": "ext_...",
                        "columns": [
                            {"name": "id", "type": "string", ...},
                            ...
                        ]
                    }
                ]
            }
        """
        if not cls.__tablename__:
            raise ValueError(f"{cls.__name__} must define __tablename__")
        if not cls.__tablename__.startswith("ext_"):
            raise ValueError(
                f"__tablename__ must start with 'ext_', got '{cls.__tablename__}'"
            )
        if not cls._fields:
            raise ValueError(f"{cls.__name__} must define at least one field")

        columns = [field.to_column_dict() for field in cls._fields]

        return {
            "tables": [
                {
                    "name": cls.__tablename__,
                    "columns": columns,
                }
            ],
        }

    @classmethod
    def register(
        cls,
        client: "AskDianaClient",
        install_id: str,
        version: str,
    ) -> Dict[str, Any]:
        """Register this model's schema with Ask DIANA.

        Shortcut for ``client.register_schema(install_id, version, cls.to_schema())``.
        """
        return client.register_schema(
            install_id=install_id,
            version=version,
            schema=cls.to_schema(),
        )

    @classmethod
    def apply(
        cls,
        client: "AskDianaClient",
        install_id: str,
    ) -> Dict[str, Any]:
        """Apply (create) this model's table in the extensions DB.

        Must be called after :meth:`register`.

        Shortcut for ``client.apply_schema(install_id, cls.__tablename__)``.
        """
        return client.apply_schema(
            install_id=install_id,
            table_name=cls.__tablename__,
        )

    @classmethod
    def setup(
        cls,
        client: "AskDianaClient",
        install_id: str,
        version: str,
    ) -> Dict[str, Any]:
        """Register and apply in one call.

        Convenience method that calls :meth:`register` then :meth:`apply`.
        """
        cls.register(client, install_id, version)
        return cls.apply(client, install_id)


# ------------------------------------------------------------------ #
# Utility                                                              #
# ------------------------------------------------------------------ #


def register_all_models(
    client: "AskDianaClient",
    install_id: str,
    version: str,
    *models: type,
) -> Dict[str, Any]:
    """Register multiple ExtModel subclasses in a single API call.

    Combines all models into one schema declaration with multiple tables.

    Example::

        register_all_models(client, install_id, "1.0.0",
                            Accounts, SyncHistory, Settings)
    """
    all_tables: List[Dict[str, Any]] = []
    for model in models:
        schema = model.to_schema()
        all_tables.extend(schema["tables"])

    combined_schema = {"tables": all_tables}
    return client.register_schema(install_id, version, combined_schema)
