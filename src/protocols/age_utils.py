"""Utilities for composing and parsing protocol age strings."""

import re

_YEAR_PATTERN = re.compile(r"^(\d+)\s+a(?:ñ|n)os?$", re.IGNORECASE)
_MONTH_PATTERN = re.compile(r"^(\d+)\s+mes(?:es)?$", re.IGNORECASE)
_COMBINED_PATTERN = re.compile(
    r"^(?:(\d+)\s+a(?:ñ|n)os?)?(?:\s+(\d+)\s+mes(?:es)?)?$",
    re.IGNORECASE,
)


def compose_age_string(
    years: int | None,
    months: int | None,
) -> str:
    """
    Build a human-readable age string for Protocol.age.

    Args:
        years: Age in full years, or None if not provided.
        months: Additional months, or None if not provided.

    Returns:
        Composed string such as "2 años 3 meses", or empty if both are zero.
    """
    y = years if years is not None else 0
    m = months if months is not None else 0

    if y == 0 and m == 0:
        return ""

    parts: list[str] = []
    if y > 0:
        parts.append(f"{y} {'año' if y == 1 else 'años'}")
    if m > 0:
        parts.append(f"{m} {'mes' if m == 1 else 'meses'}")
    return " ".join(parts)


def parse_age_string(value: str) -> tuple[int | None, int | None]:
    """
    Parse a stored age string into years and months components.

    Args:
        value: Stored age text from Protocol.age.

    Returns:
        Tuple of (years, months); each element is None when not present.
        Returns (None, None) for empty or unparseable legacy values.
    """
    if not value or not value.strip():
        return None, None

    text = value.strip()

    combined = _COMBINED_PATTERN.match(text)
    if combined and (combined.group(1) or combined.group(2)):
        years = int(combined.group(1)) if combined.group(1) else None
        months = int(combined.group(2)) if combined.group(2) else None
        return years, months

    year_match = _YEAR_PATTERN.match(text)
    if year_match:
        return int(year_match.group(1)), None

    month_match = _MONTH_PATTERN.match(text)
    if month_match:
        return None, int(month_match.group(1))

    return None, None
