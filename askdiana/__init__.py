"""Ask DIANA Extension SDK."""

from .chat import ChatService
from .client import AskDianaClient
from .connector import ConnectorService
from .context import ContextError, Persona, RequestContext, verify_context
from .models import (
    BooleanField,
    DateField,
    DateTimeField,
    ExtModel,
    Field,
    FloatField,
    IntegerField,
    JsonField,
    StringField,
    TextField,
    register_all_models,
)
from .service import ExtensionService
from .webhooks import WebhookVerificationError, verify_bearer_token, verify_webhook

__all__ = [
    "AskDianaClient",
    "BooleanField",
    "ChatService",
    "ConnectorService",
    "ContextError",
    "DateField",
    "DateTimeField",
    # Models
    "ExtModel",
    # Services
    "ExtensionService",
    "Field",
    "FloatField",
    "IntegerField",
    "JsonField",
    "Persona",
    "RequestContext",
    "StringField",
    "TextField",
    "WebhookVerificationError",
    "register_all_models",
    "verify_bearer_token",
    # Who is using the extension, in which persona
    "verify_context",
    "verify_webhook",  # deprecated — use verify_bearer_token
]

# Flask-dependent imports (optional — requires `pip install askdiana[app]`)
try:
    from .app import ExtensionApp
    from .controller import install_id_required, webhook_required

    __all__ += [
        "ExtensionApp",
        "install_id_required",
        "webhook_required",
    ]
except ImportError:
    pass

__version__ = "0.1.0"
