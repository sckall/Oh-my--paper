"""Shared helpers for journal-research adapters (EN + CN unified)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MAILTO = os.getenv("CROSSREF_MAILTO") or os.getenv("JOURNAL_RESEARCH_MAILTO")
USER_AGENT = "oh-my-paper/journal-research"
if DEFAULT_MAILTO:
    USER_AGENT = f"{USER_AGENT} (mailto:{DEFAULT_MAILTO})"
OPENALEX_BASE = "https://api.openalex.org"
ISSN_RE = re.compile(r"^\d{4}-?\d{3}[\dXx]$")


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def plugin_root_from_script(script_file: str) -> Path:
    return Path(script_file).resolve().parents[3]


def normalize_issn(value: str | None) -> str | None:
    if not value:
        return None
    compact = value.strip().replace("-", "").upper()
    if not ISSN_RE.match(compact):
        return value.strip()
    return f"{compact[:4]}-{compact[4:]}"


def normalize_journal_name(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"\s+", "", value)
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"[\u3000:：;；,，。]+$", "", text)
    if text.count("(") > text.count(")") and not text.endswith(")"):
        text = f"{text})"
    return text.strip()


def read_key(env_name: str, keychain_service: str | None = None) -> str | None:
    value = os.getenv(env_name)
    if value:
        return value.strip() or None
    if not keychain_service:
        return None
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", keychain_service, "-w"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def build_url(url: str, params: dict[str, Any] | None = None) -> str:
    if not params:
        return url
    clean = {key: value for key, value in params.items() if value not in (None, "", [])}
    query = urllib.parse.urlencode(clean, doseq=True)
    if not query:
        return url
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}{query}"


def request_bytes(
    url: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 20,
    retries: int = 3,
    backoff: float = 1.0,
) -> bytes:
    target = build_url(url, params)
    request_headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        request_headers.update(headers)
    body = None
    last_error: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(target, data=body, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            err_body = exc.read()[:300]
            last_error = RuntimeError(f"HTTP {exc.code} for {target}: {err_body!r}")
            if exc.code < 500 and exc.code not in (408, 429):
                raise last_error
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        if attempt < retries - 1:
            time.sleep(backoff * (2**attempt))
    raise RuntimeError(f"request failed for {target}: {last_error}")


def decode_chinese_html(value: bytes) -> str:
    for encoding in ("utf-8", "gb18030", "gbk", "gb2312"):
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            continue
    return value.decode("utf-8", errors="replace")


def request_text(
    url: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    retries: int = 3,
    timeout: float = 20,
    backoff: float = 1.0,
) -> str:
    body_bytes = None
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    if payload is not None:
        body_bytes = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
        request_headers.setdefault("Accept", "application/json")
    target = build_url(url, params)
    last_error: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(target, data=body_bytes, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
                return decode_chinese_html(raw)
        except urllib.error.HTTPError as exc:
            err_body = exc.read()[:300]
            last_error = RuntimeError(f"HTTP {exc.code} for {target}: {err_body!r}")
            if exc.code < 500 and exc.code not in (408, 429):
                raise last_error
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        if attempt < retries - 1:
            time.sleep(backoff * (2**attempt))
    raise RuntimeError(f"request failed for {target}: {last_error}")


def request_json(
    url: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    retries: int = 3,
    timeout: float = 20,
    backoff: float = 1.0,
) -> dict[str, Any]:
    text = request_text(
        url,
        method=method,
        params=params,
        payload=payload,
        headers=headers,
        retries=retries,
        timeout=timeout,
        backoff=backoff,
    )
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON from {url}: {text[:300]}") from exc
    if not isinstance(result, dict):
        raise RuntimeError(f"unexpected JSON shape from {url}")
    return result


# ── OpenAlex helpers (EN route) ──────────────────────────────────────────


def openalex_api_key() -> str | None:
    env_key = os.getenv("OPENALEX_API_KEY")
    if env_key:
        return env_key.strip() or None
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "openalex", "-w"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    key = result.stdout.strip()
    return key or None


def openalex_params(params: dict[str, Any] | None = None, *, mailto: str | None = None) -> dict[str, Any]:
    merged = dict(params or {})
    key = openalex_api_key()
    if key:
        merged["api_key"] = key
    if mailto or DEFAULT_MAILTO:
        merged["mailto"] = mailto or DEFAULT_MAILTO
    return merged


def openalex_short_id(source_id: str) -> str:
    return source_id.rstrip("/").split("/")[-1]


# ── Evidence / Candidate builders ─────────────────────────────────────────


def source_evidence(source: str, url: str | None, trust_level: str, tool_tier_used: str = "2") -> dict[str, Any]:
    return {
        "source": source,
        "url": url,
        "access_level": "public",
        "trust_level": trust_level,
        "fetched_at": utc_now(),
        "raw_snippet_path": None,
        "tool_tier_used": tool_tier_used,
        "notes": [],
    }


def candidate(
    *,
    title: str,
    issn: str | None = None,
    eissn: str | None = None,
    publisher: str | None = None,
    official_site: str | None = None,
    fit_score: float | None = None,
    authority_metrics: dict[str, Any] | None = None,
    speed_intel: dict[str, Any] | None = None,
    cost_intel: dict[str, Any] | None = None,
    risk_flags: list[str] | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "identity": {
            "title": title,
            "issn": normalize_issn(issn),
            "eissn": normalize_issn(eissn),
            "publisher": publisher,
            "country": None,
            "language": None,
            "official_site": official_site,
            "submission_site": None,
            "wos_categories": [],
            "scie_status": None,
            "ssci_status": None,
        },
        "fit_score": fit_score,
        "authority_metrics": authority_metrics or {},
        "cas_legacy": None,
        "cas_letpub": None,
        "review_intel": {},
        "speed_intel": speed_intel or {},
        "cost_intel": cost_intel or {},
        "risk_flags": risk_flags or [],
        "evidence": evidence or [],
    }


def candidate_journal(
    title_cn: str,
    *,
    issn: str | None = None,
    cn_number: str | None = None,
    title_en: str | None = None,
    catalog_labels: list[str] | None = None,
    fit_score: float | None = None,
    rank_profile: dict[str, Any] | None = None,
    review_intel: dict[str, Any] | None = None,
    risk_flags: list[str] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    trust_level: str = "catalog-cn",
) -> dict[str, Any]:
    return {
        "identity": {
            "title_cn": title_cn,
            "title_en": title_en,
            "issn": normalize_issn(issn),
            "cn_number": cn_number,
            "host_org": None,
            "publisher": None,
            "catalog_labels": catalog_labels or [],
            "official_site": None,
            "submission_site": None,
        },
        "fit_score": fit_score,
        "rank_profile": rank_profile or {},
        "review_intel": review_intel or {},
        "evidence_completeness": "partial",
        "risk_flags": risk_flags or [],
        "trust_level": trust_level,
        "evidence": evidence or [],
    }


def openalex_source_candidate(
    source: dict[str, Any],
    *,
    fit_score: float | None,
    evidence_source: str,
    trust_level: str,
    evidence_url: str | None = None,
    extra_authority: dict[str, Any] | None = None,
) -> dict[str, Any]:
    issns = [normalize_issn(item) for item in ensure_list(source.get("issn")) if item]
    issn_l = normalize_issn(source.get("issn_l")) or (issns[0] if issns else None)
    eissn = next((item for item in issns if item and item != issn_l), None)
    metrics = {
        "openalex": {
            "id": source.get("id"),
            "type": source.get("type"),
            "is_oa": source.get("is_oa"),
            "is_in_doaj": source.get("is_in_doaj"),
            "works_count": source.get("works_count"),
            "cited_by_count": source.get("cited_by_count"),
            "summary_stats": source.get("summary_stats") or {},
        }
    }
    if extra_authority:
        metrics.update(extra_authority)
    return candidate(
        title=source.get("display_name") or source.get("title") or "Unknown source",
        issn=issn_l,
        eissn=eissn,
        publisher=source.get("host_organization_name"),
        official_site=source.get("homepage_url"),
        fit_score=fit_score,
        authority_metrics=metrics,
        cost_intel={"apc_usd": source.get("apc_usd"), "apc_prices": source.get("apc_prices") or []},
        evidence=[source_evidence(evidence_source, evidence_url or source.get("id"), trust_level)],
    )


def openalex_get_source(source_id: str, *, mailto: str | None = None) -> dict[str, Any]:
    short_id = openalex_short_id(source_id)
    return request_json(f"{OPENALEX_BASE}/sources/{short_id}", params=openalex_params({}, mailto=mailto))


def openalex_search_sources(query: str, *, limit: int = 1, mailto: str | None = None) -> list[dict[str, Any]]:
    data = request_json(
        f"{OPENALEX_BASE}/sources",
        params=openalex_params({"search": query, "per-page": limit}, mailto=mailto),
    )
    return data.get("results") or []


def openalex_group_journals(
    query: str,
    *,
    per_page: int = 10,
    mailto: str | None = None,
    filter_extra: str | None = None,
    evidence_source: str = "openalex-group-by-source",
    trust_level: str = "openalex-explore",
) -> list[dict[str, Any]]:
    filters = ["primary_location.source.type:journal"]
    if filter_extra:
        filters.append(filter_extra)
    params = {
        "search": query,
        "filter": ",".join(filters),
        "group_by": "primary_location.source.id",
        "per-page": per_page,
    }
    data = request_json(f"{OPENALEX_BASE}/works", params=openalex_params(params, mailto=mailto))
    groups = data.get("group_by") or []
    top_count = max([int(group.get("count") or 0) for group in groups] or [1])
    candidates: list[dict[str, Any]] = []
    for group in groups[:per_page]:
        key = group.get("key")
        if not key:
            continue
        source = openalex_get_source(key, mailto=mailto)
        source_type = (source.get("type") or "").lower()
        if source_type and source_type != "journal":
            continue
        count = int(group.get("count") or 0)
        candidates.append(
            openalex_source_candidate(
                source,
                fit_score=round(count / top_count, 4) if top_count else None,
                evidence_source=evidence_source,
                trust_level=trust_level,
                evidence_url=key,
                extra_authority={"openalex_group_count": count},
            )
        )
        time.sleep(0.1)
    return candidates


# ── TokenBucket (CN rate limiting) ────────────────────────────────────────


class TokenBucket:
    """Small in-process token bucket for public adapter rate limits."""

    def __init__(self, *, rate_per_second: float, capacity: int = 1) -> None:
        self.rate_per_second = rate_per_second
        self.capacity = max(capacity, 1)
        self.tokens = float(self.capacity)
        self.updated = time.monotonic()

    def wait(self, tokens: float = 1.0) -> None:
        while True:
            now = time.monotonic()
            elapsed = now - self.updated
            self.updated = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_second)
            if self.tokens >= tokens:
                self.tokens -= tokens
                return
            missing = tokens - self.tokens
            time.sleep(missing / self.rate_per_second)


# ── JSON output ────────────────────────────────────────────────────────────


def write_json(data: dict[str, Any], output: str | None = None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if output:
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text, end="")
