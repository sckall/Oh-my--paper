"""Shared API helpers for journal-research-en adapter scripts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


DEFAULT_MAILTO = os.getenv("CROSSREF_MAILTO") or os.getenv("JOURNAL_RESEARCH_MAILTO")
DEFAULT_USER_AGENT = "journal-research-en/0.2.0"
if DEFAULT_MAILTO:
    DEFAULT_USER_AGENT = f"{DEFAULT_USER_AGENT} (mailto:{DEFAULT_MAILTO})"


def add_plugin_root_to_path(file_path: str) -> Path:
    """Add the plugin root to sys.path and return it."""
    current = Path(file_path).resolve()
    for parent in current.parents:
        if (parent / "_shared").is_dir() and (parent / "skills").is_dir():
            root = str(parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            return parent
    raise RuntimeError(f"could not locate journal-research-en root from {file_path}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def load_openalex_api_key() -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    env_value = os.environ.get("OPENALEX_API_KEY")
    if env_value:
        return env_value.strip(), warnings

    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "openalex", "-w"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        warnings.append(f"OpenAlex Keychain lookup skipped: {exc}")
        return None, warnings

    key = result.stdout.strip()
    if result.returncode == 0 and key:
        return key, warnings
    warnings.append("OPENALEX_API_KEY not set and Keychain service 'openalex' not found; using anonymous OpenAlex pool")
    return None, warnings


def request_json(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    retries: int = 3,
    backoff: float = 1.0,
) -> dict[str, Any]:
    session = requests.Session()
    merged_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        merged_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = session.request(
                method,
                url,
                params=params,
                json=json_body,
                headers=merged_headers,
                timeout=timeout,
            )
            if response.status_code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                retry_after = response.headers.get("Retry-After")
                sleep_for = float(retry_after) if retry_after and retry_after.isdigit() else backoff * (2**attempt)
                time.sleep(sleep_for)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # requests raises several subclasses.
            last_error = exc
            if attempt < retries - 1:
                time.sleep(backoff * (2**attempt))
                continue
            raise

    assert last_error is not None
    raise last_error


def openalex_params(extra: dict[str, Any] | None = None, *, mailto: str | None = None) -> tuple[dict[str, Any], list[str]]:
    params: dict[str, Any] = {}
    warnings: list[str] = []
    if extra:
        params.update(extra)
    api_key, key_warnings = load_openalex_api_key()
    warnings.extend(key_warnings)
    if api_key:
        params["api_key"] = api_key
    if mailto:
        params["mailto"] = mailto
    return params, warnings


def openalex_entity_id(value: str | None) -> str | None:
    if not value:
        return None
    return value.rstrip("/").split("/")[-1]


def normalize_issns(values: Any) -> tuple[str | None, str | None]:
    if not values:
        return None, None
    if isinstance(values, str):
        return values, None
    if not isinstance(values, list):
        return None, None
    issns = [str(v) for v in values if v]
    if not issns:
        return None, None
    return issns[0], issns[1] if len(issns) > 1 else None


def source_to_candidate(
    source: dict[str, Any],
    *,
    fit_score: float | None = None,
    evidence_source: str,
    evidence_url: str | None = None,
    trust_level: str = "explore-adapter",
    extra_metrics: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    issn, eissn = normalize_issns(source.get("issn") or source.get("issns"))
    if not issn:
        issn = source.get("issn_l") or source.get("pissn")
    if not eissn:
        eissn = source.get("eissn")

    identity = {
        "title": source.get("display_name") or source.get("title") or source.get("name"),
        "issn": issn,
        "eissn": eissn,
        "publisher": source.get("host_organization_name") or source.get("publisher_name") or source.get("publisher"),
        "country": source.get("country_code") or source.get("publisher_country"),
        "language": None,
        "official_site": source.get("homepage_url") or source.get("ref_journal"),
        "submission_site": source.get("ref_author_instructions"),
        "wos_categories": [],
        "scie_status": None,
        "ssci_status": None,
    }
    authority_metrics = {
        "openalex_id": source.get("id"),
        "source_type": source.get("type"),
        "is_oa": source.get("is_oa"),
        "is_in_doaj": source.get("is_in_doaj") if "is_in_doaj" in source else source.get("doaj_seal"),
        "works_count": source.get("works_count"),
        "cited_by_count": source.get("cited_by_count"),
        "summary_stats": source.get("summary_stats"),
    }
    if extra_metrics:
        authority_metrics.update(extra_metrics)
    return {
        "identity": identity,
        "fit_score": fit_score,
        "authority_metrics": authority_metrics,
        "cas_legacy": None,
        "cas_letpub": None,
        "review_intel": {},
        "speed_intel": {},
        "cost_intel": {},
        "risk_flags": [],
        "evidence": [
            {
                "source": evidence_source,
                "url": evidence_url,
                "access_level": "public",
                "trust_level": trust_level,
                "fetched_at": now_iso(),
                "raw_snippet_path": None,
                "tool_tier_used": "script",
                "notes": warnings or [],
            }
        ],
    }


def print_payload(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def die(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)
