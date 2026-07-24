"""
Mail-merge personalization.

Templates use ``{{ field }}`` tokens (whitespace-insensitive) that are replaced
per recipient from a dict of named fields — e.g. ``Hi {{name}}`` with
``{"name": "Alice"}`` renders ``Hi Alice``.

Kept dependency-free and deliberately simple: only ``{{token}}`` substitution,
no expressions, filters, or logic (this is a mailer, not a template engine).
"""

import re

# Matches {{ field }} with optional surrounding whitespace. Field names are
# word-ish: letters, digits, underscores, spaces, dots, hyphens.
_TOKEN_RE = re.compile(r"\{\{\s*([\w .\-]+?)\s*\}\}")


def extract_fields(*texts: str) -> list[str]:
    """Return the unique field names referenced across the given texts (in order)."""
    seen: list[str] = []
    for text in texts:
        for match in _TOKEN_RE.finditer(text or ""):
            name = match.group(1).strip()
            if name not in seen:
                seen.append(name)
    return seen


def has_tokens(*texts: str) -> bool:
    """True if any of the texts contain at least one ``{{token}}``."""
    return any(_TOKEN_RE.search(t or "") for t in texts)


def render(template: str, fields: dict) -> str:
    """
    Substitute ``{{token}}`` occurrences in ``template`` from ``fields``.

    Field lookup is case-insensitive on the key. Unknown tokens are replaced with
    an empty string (use :func:`missing_fields` beforehand to detect/report them).
    """
    if not template:
        return template
    lookup = {str(k).strip().lower(): "" if v is None else str(v) for k, v in fields.items()}

    def _sub(match: re.Match) -> str:
        return lookup.get(match.group(1).strip().lower(), "")

    return _TOKEN_RE.sub(_sub, template)


def missing_fields(fields: dict, required: list[str]) -> list[str]:
    """
    Return required field names that are absent or blank in ``fields``.

    Comparison is case-insensitive. Used to warn (not crash) before a
    personalized send.
    """
    present = {
        str(k).strip().lower()
        for k, v in fields.items()
        if v is not None and str(v).strip() != ""
    }
    return [name for name in required if name.strip().lower() not in present]
