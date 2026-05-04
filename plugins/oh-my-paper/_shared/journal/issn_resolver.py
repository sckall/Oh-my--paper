"""ISSN helpers for English journal research."""

from __future__ import annotations

import re
from dataclasses import dataclass


ISSN_RE = re.compile(r"^\d{4}-?\d{3}[\dXx]$")


@dataclass(frozen=True, slots=True)
class LetPubJournalRef:
    issn: str
    letpub_id: str
    title: str | None = None


def normalize_issn(value: str) -> str:
    compact = value.strip().replace("-", "").upper()
    if not ISSN_RE.match(compact):
        raise ValueError(f"invalid ISSN: {value!r}")
    return f"{compact[:4]}-{compact[4:]}"


def resolve_letpub_id(issn: str, mapping: dict[str, LetPubJournalRef | str]) -> str | None:
    normalized = normalize_issn(issn)
    entry = mapping.get(normalized) or mapping.get(normalized.replace("-", ""))
    if isinstance(entry, LetPubJournalRef):
        return entry.letpub_id
    return entry
