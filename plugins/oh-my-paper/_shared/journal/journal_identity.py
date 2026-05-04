"""Shared journal identity models for journal-research-en."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceEvidence:
    source: str
    url: str | None = None
    access_level: str = "public"
    trust_level: str = "unknown"
    fetched_at: str | None = None
    raw_snippet_path: str | None = None
    tool_tier_used: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class JournalIdentity:
    title: str
    issn: str | None = None
    eissn: str | None = None
    publisher: str | None = None
    country: str | None = None
    language: str | None = None
    official_site: str | None = None
    submission_site: str | None = None
    wos_categories: list[str] = field(default_factory=list)
    scie_status: str | None = None
    ssci_status: str | None = None


@dataclass(slots=True)
class CandidateJournal:
    identity: JournalIdentity
    fit_score: float | None = None
    authority_metrics: dict[str, Any] = field(default_factory=dict)
    cas_legacy: dict[str, Any] | None = None
    cas_letpub: dict[str, Any] | None = None
    review_intel: dict[str, Any] = field(default_factory=dict)
    speed_intel: dict[str, Any] = field(default_factory=dict)
    cost_intel: dict[str, Any] = field(default_factory=dict)
    risk_flags: list[str] = field(default_factory=list)
    evidence: list[SourceEvidence] = field(default_factory=list)
