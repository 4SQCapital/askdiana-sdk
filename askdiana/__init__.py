"""Ask DIANA Extension SDK."""

from .client import AskDianaClient
from .webhooks import verify_webhook, WebhookVerificationError
from .models import (
    ExtModel,
    Field,
    StringField,
    TextField,
    IntegerField,
    FloatField,
    BooleanField,
    DateTimeField,
    DateField,
    JsonField,
    register_all_models,
)
from .service import ExtensionService
from .connector import ConnectorService
from .chat import ChatService

__all__ = [
    "AskDianaClient",
    "verify_webhook",
    "WebhookVerificationError",
    # Models
    "ExtModel",
    "Field",
    "StringField",
    "TextField",
    "IntegerField",
    "FloatField",
    "BooleanField",
    "DateTimeField",
    "DateField",
    "JsonField",
    "register_all_models",
    # Services
    "ExtensionService",
    "ConnectorService",
    "ChatService",
]

# Flask-dependent imports (optional — requires `pip install askdiana[app]`)
try:
    from .app import ExtensionApp
    from .controller import webhook_required, install_id_required

    __all__ += [
        "ExtensionApp",
        "webhook_required",
        "install_id_required",
    ]
except ImportError:
    pass

__version__ = "0.4.0"
