"""Encoding helpers for English journal-research sources."""

from __future__ import annotations


UTF8_BOM = "\ufeff"


def normalize_utf8_text(value: bytes | str) -> str:
    """Return UTF-8 text with a leading BOM removed."""
    if isinstance(value, bytes):
        text = value.decode("utf-8-sig", errors="replace")
    else:
        text = value.lstrip(UTF8_BOM)
    return text.replace("\r\n", "\n").replace("\r", "\n")
