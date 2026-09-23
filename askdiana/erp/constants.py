from __future__ import annotations

import re

# --- Environment variable names --------------------------------------------
ENV_LLM_PROVIDER = "LLM_PROVIDER"
ENV_LLM_URL = "LLM_URL"
ENV_LLM_API_KEY = "LLM_API_KEY"
ENV_LLM_MODEL = "LLM_MODEL"
ENV_DEMO_WHEN_DISCONNECTED = "DEMO_WHEN_DISCONNECTED"
ENV_CACHE_TTL_SECONDS = "ERP_CACHE_TTL_SECONDS"
ENV_PUBLIC_URL = "EXTENSION_PUBLIC_URL"
ENV_ALLOW_INSECURE_URLS = "ERP_ALLOW_INSECURE_URLS"

LEGACY_LLM_ENV = {
    ENV_LLM_URL: "GENIUS2_URL",
    ENV_LLM_API_KEY: "GENIUS2_API_KEY",
    ENV_LLM_MODEL: "GENIUS2_MODEL",
}

DEFAULT_DEMO_WHEN_DISCONNECTED = True
DEFAULT_CACHE_TTL_SECONDS = 300
DEFAULT_ALLOW_INSECURE_URLS = False

# --- HTTP --------------------------------------------------------------------
HTTP_TIMEOUT_SECONDS = 15
LLM_TIMEOUT_SECONDS = 60
HTTP_UNAUTHORIZED = 401
HTTP_TOO_MANY_REQUESTS = 429
HTTP_CLIENT_ERROR_MIN = 400
AUTH_REJECTED_STATUSES = frozenset({401, 403})
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_SECONDS = 1.0
RETRY_MAX_DELAY_SECONDS = 20.0
ERROR_BODY_PREVIEW_CHARS = 300
SECURE_URL_SCHEMES = frozenset({"https"})
DEV_URL_SCHEMES = frozenset({"http", "https"})
DEFAULT_HTTPS_PORT = 443

# --- LLM ---------------------------------------------------------------------
PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
DEFAULT_LLM_PROVIDER = PROVIDER_OPENAI
ANTHROPIC_API_VERSION = "2023-06-01"
LLM_MAX_TOKENS = 4096
LLM_TEMPERATURE = 0.2

# --- Login methods (pack `auth:` keys) ------------------------------------------
AUTH_OAUTH2, AUTH_TOKEN, AUTH_BASIC, AUTH_SESSION = "oauth2", "token", "basic", "session"
AUTH_METHODS = (AUTH_OAUTH2, AUTH_TOKEN, AUTH_BASIC, AUTH_SESSION)
CREDENTIAL_METHODS = frozenset({AUTH_TOKEN, AUTH_BASIC, AUTH_SESSION})

INPUT_TEXT, INPUT_URL, INPUT_SECRET = "text", "url", "secret"
INPUT_KINDS = frozenset({INPUT_TEXT, INPUT_URL, INPUT_SECRET})

SESSION_FROM_COOKIE, SESSION_FROM_BODY = "cookie", "body"
SESSION_SOURCES = frozenset({SESSION_FROM_COOKIE, SESSION_FROM_BODY})
SESSION_PLACEHOLDER = "session"
DEFAULT_SESSION_TTL_SECONDS = 1200

# --- OAuth -------------------------------------------------------------------
TOKEN_ACCESS = "access_token"
TOKEN_REFRESH = "refresh_token"
TOKEN_EXPIRES_IN = "expires_in"
TOKEN_EXPIRES_AT = "expires_at"
TOKEN_ACCOUNT_LABEL = "account_email"
TOKEN_AUTH_SERVER = "accounts_url"
TOKEN_AUTH_METHOD = "auth_method"
TOKEN_CREDENTIALS = "credentials"
TOKEN_REFRESH_LEEWAY_SECONDS = 60
GRANT_AUTHORIZATION_CODE = "authorization_code"
GRANT_REFRESH_TOKEN = "refresh_token"

# --- Connect page (token / basic / session) -----------------------------------------
CONNECT_PAGE_PATH = "/connect"
CONNECT_API_PATH = "/api/connect"
CONNECT_NAMESPACE = "erp_connect"
CONNECT_NONCE_KEY = "nonce"
CONNECT_NONCE_BYTES = 24
CONNECT_NONCE_TTL_SECONDS = 600
CONNECTED_CODE = "credentials-saved"

# --- Install modes -------------------------------------------------------------
MODE_LIVE = "live"
MODE_DEMO = "demo"
MODE_DISCONNECTED = "disconnected"

# --- Query engine -------------------------------------------------------------
OP_EQ, OP_NEQ = "eq", "neq"
OP_GT, OP_GTE, OP_LT, OP_LTE = "gt", "gte", "lt", "lte"
OP_CONTAINS, OP_IN, OP_NOT_IN = "contains", "in", "not_in"
OPERATORS = frozenset({OP_EQ, OP_NEQ, OP_GT, OP_GTE, OP_LT, OP_LTE, OP_CONTAINS, OP_IN, OP_NOT_IN})
PRESENTER_OPERATORS = (OP_GT, OP_GTE, OP_LT, OP_LTE, OP_EQ, OP_NEQ, OP_CONTAINS)

AGG_SUM, AGG_COUNT, AGG_AVG, AGG_COUNT_DISTINCT = "sum", "count", "avg", "count_distinct"
AGGREGATIONS = frozenset({AGG_SUM, AGG_COUNT, AGG_AVG, AGG_COUNT_DISTINCT})
PRESENTER_AGGREGATIONS = (AGG_SUM, AGG_COUNT, AGG_AVG)

FIELD_ID, FIELD_STRING, FIELD_NUMBER = "id", "string", "number"
FIELD_MONEY, FIELD_PERCENT, FIELD_DATE = "money", "percent", "date"
FIELD_TYPES = frozenset({FIELD_ID, FIELD_STRING, FIELD_NUMBER, FIELD_MONEY, FIELD_PERCENT, FIELD_DATE})

CHART_BAR, CHART_HBAR, CHART_LINE = "bar", "horizontal_bar", "line"
CHART_AREA, CHART_DONUT, CHART_PIE = "area", "donut", "pie"
CHART_TYPES = (CHART_HBAR, CHART_BAR, CHART_LINE, CHART_AREA, CHART_DONUT, CHART_PIE)

FMT_CURRENCY, FMT_CURRENCY_COMPACT = "currency", "currency_compact"
FMT_PERCENT, FMT_NUMBER, FMT_DECIMAL1 = "percent", "number", "decimal1"
FORMATS = frozenset({FMT_CURRENCY, FMT_CURRENCY_COMPACT, FMT_PERCENT, FMT_NUMBER, FMT_DECIMAL1})
COMPACT_MILLION = 1_000_000
COMPACT_THOUSAND = 1_000

VARIANT_DEFAULT = "default"
VARIANTS = frozenset({VARIANT_DEFAULT, "success", "warning", "danger"})

SET_REFERENCE_PREFIX = "$"

# --- Chat answers ---------------------------------------------------------------
DEFAULT_TOP_N = 5
MIN_CHAT_CHART_GROUPS = 2
TABLE_DISPLAY_CAP = 100
TABLE_PAGE_SIZE = 10
FALLBACK_TABLE_MAX_COLUMNS = 6
MAX_PLANNER_ENDPOINTS = 4
INTENT_OUT_OF_SCOPE = "out_of_scope"
INTENT_GENERAL = "general_overview"
EXPORT_CSV_PATH = "/api/extensions/export-csv"
PLACEHOLDER_RE = re.compile(r"[A-Z]{2,}(?:_[A-Z]{2,})+|\$[A-Z]\b|\b[A-Z]\b")

