"""Secret redaction for anything that could reach a tool result or log line.

Applied to: execution stdout/stderr, exception tracebacks, audit log entries.
Errs on the side of over-redaction.
"""
from __future__ import annotations

import re

_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd|access[_-]?key)(\s*[=:]\s*)([^\s'\"]+)"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),  # Google API key
    re.compile(r"ya29\.[0-9A-Za-z\-_]+"),  # Google OAuth access token
    re.compile(r"gh[pousr]_[0-9A-Za-z]{36,}"),  # GitHub tokens
    re.compile(r"sk-[0-9A-Za-z]{20,}"),  # generic sk- style API keys
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.S),
]

_REDACTED = "[REDACTED]"


def redact_secrets(text: str) -> str:
    if not text:
        return text

    def _kv_sub(match: re.Match) -> str:
        return f"{match.group(1)}{match.group(2)}{_REDACTED}"

    out = _PATTERNS[0].sub(_kv_sub, text)
    for pattern in _PATTERNS[1:]:
        out = pattern.sub(_REDACTED, out)
    return out
