"""
Base class for extension services.

Services encapsulate business logic and interact with the Ask DIANA API
through the client.  They mirror the backend pattern where service classes
receive a SQLAlchemy ``Session`` — here they receive an ``AskDianaClient``
instead, since extensions do not have direct DB access.

Usage::

    from askdiana import ExtensionService

    class TaskService(ExtensionService):
        def create_task(self, install_id, title, priority=3):
            self.client.set_data(install_id, "tasks", title, {"priority": priority})
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import AskDianaClient


class ExtensionService:
    """Base class for extension service layer.

    Subclass this and implement your business logic.  The ``client``
    attribute provides access to the Ask DIANA Extension API.
    """

    def __init__(self, client: "AskDianaClient"):
        self.client = client
