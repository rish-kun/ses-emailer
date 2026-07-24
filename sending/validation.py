"""
Email address validation and list helpers.

Kept intentionally dependency-free and permissive: the goal is to catch obvious
junk (empty cells, header labels, malformed strings) before addresses are handed
to SES, not to be an RFC-5322 oracle.
"""

import re

# Pragmatic address pattern: local@domain.tld, no spaces, at least one dot in the
# domain. Deliberately simpler than full RFC 5322.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: object) -> str:
    """Coerce an arbitrary cell/value to a trimmed, lowercased email string."""
    return str(value).strip().lower()


def is_valid_email(value: object) -> bool:
    """Return True if ``value`` looks like a valid email address."""
    return bool(_EMAIL_RE.match(normalize_email(value)))


def partition_valid(values: list) -> tuple[list[str], list[str]]:
    """
    Split an iterable of candidate addresses into (valid, invalid).

    Values are normalized (str/strip/lower) and de-duplicated while preserving
    first-seen order. Empty values are dropped entirely (neither valid nor
    invalid).
    """
    valid: list[str] = []
    invalid: list[str] = []
    seen: set[str] = set()
    for raw in values:
        email = normalize_email(raw)
        if not email:
            continue
        if email in seen:
            continue
        seen.add(email)
        if is_valid_email(email):
            valid.append(email)
        else:
            invalid.append(email)
    return valid, invalid
