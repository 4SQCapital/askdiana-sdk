from __future__ import annotations


class ErpError(Exception):
    NOT_CONNECTED = "not_connected"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMITED = "rate_limited"
    VENDOR = "vendor_error"
    NOT_FOUND = "not_found"
    INVALID = "invalid_input"
    CONFIG = "config_error"
    
    HTTP_STATUS = {  # noqa: RUF012
        NOT_CONNECTED: 409,
        UNAUTHORIZED: 401,
        RATE_LIMITED: 429,
        VENDOR: 502,
        NOT_FOUND: 404,
        INVALID: 400,
        CONFIG: 500,
    }
    
    def __init__(self, kind: str, message: str, *, vendor_status: int | None = None):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.vendor_status = vendor_status
        
    @property
    def http_status(self) -> int:
        return self.HTTP_STATUS.get(self.kind, 500)
    
    def to_dict(self) -> dict:
        return {"error": self.message, "kind": self.kind}
