from __future__ import annotations

import re

# Patterns for secrets/tokens/keys. Replacement is always ***.
_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
    ),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|password|token|passwd)\s*[:=]\s*\S+"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
)


def redact(text: str, replacement: str = "***") -> str:
    """Replace secret-like substrings. Empty/None-safe: non-str returns as-is via str()."""
    if not text:
        return text
    out = text
    for pat in _PATTERNS:
        out = pat.sub(replacement, out)
    return out
