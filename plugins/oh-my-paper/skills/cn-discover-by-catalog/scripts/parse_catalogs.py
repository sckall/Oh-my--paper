#!/usr/bin/env python3
"""Parse downloaded Chinese journal catalog PDFs into a normalized JSON schema."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT))

from _shared.adapter_utils import normalize_issn, normalize_journal_name, source_evidence, utc_now  # noqa: E402


CATALOG_META = {
    "pku-core-2023": {"label": "pku", "year": "2023", "type": "北大核心"},
    "cssci-2023-2024": {"label": "cssci", "year": "2023-2024", "type": "CSSCI"},
    "cscd-2023-2024": {"label": "cscd", "year": "2023-2024", "type": "CSCD"},
    "cstpcd-2024": {"label": "cstpcd", "year": "2024", "type": "中国科技核心"},
}
JOURNAL_SUFFIX_RE = re.compile(r"([\u4e00-\u9fa5A-Za-z0-9·（）()《》]{2,40}(?:学报|研究|杂志|论坛|评论|科学|技术|医学|大学学报|报|刊|通讯|导刊|世界|管理))")
ISSN_RE = re.compile(r"\b\d{4}-?\d{3}[\dXx]\b")
NOISE_TITLE_TOKENS = (
    "序号",
    "期刊名称",
    "学科名称",
    "学科分类",
    "核心库",
    "扩展库",
    "来源期刊",
    "期刊目录",
    "拟收录",
    "总览",
    "高校学报",
    "综合性人文",
)


def load_pdfplumber():
    try:
        import pdfplumber  # type: ignore
    except ImportError as exc:
        raise SystemExit("missing dependency: pip install pdfplumber") from exc
    return pdfplumber


def clean_cell(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def rows_from_pdf(path: Path) -> list[list[str]]:
    pdfplumber = load_pdfplumber()
    rows: list[list[str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                for row in table or []:
                    cleaned = [clean_cell(cell) for cell in row or []]
                    if any(cleaned):
                        rows.append(cleaned)
            if tables:
                continue
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = clean_cell(line)
                if line:
                    rows.append([line])
    return rows


def clean_title(value: str) -> str:
    text = clean_cell(value)
    text = text.replace("．", ".").replace(". ", ".").replace(" .", ".")
    text = re.sub(r"^\d+\s*", "", text)
    text = re.split(r"[，,；;]", text, maxsplit=1)[0]
    text = text.strip("《》 ")
    return normalize_journal_name(text)


def is_noise_title(value: str) -> bool:
    if not value or value.isdigit():
        return True
    if any(token in value for token in NOISE_TITLE_TOKENS):
        return True
    if "/" in value or "\\" in value:
        return True
    if len(value) < 2 or len(value) > 48:
        return True
    if not re.search(r"[\u4e00-\u9fa5]", value):
        return True
    return False


def title_cells_for_row(row: list[str], catalog_name: str) -> list[str]:
    if catalog_name == "pku-core-2023" and len(row) >= 3:
        return [row[2]]
    if catalog_name == "cssci-2023-2024" and len(row) >= 2:
        return [row[1]]
    if catalog_name == "cscd-2023-2024":
        return [
            cell
            for cell in row
            if any(token in cell for token in ("学报", "杂志", "科学", "医学", "研究", "技术", "大学", "农业", "地理", "地质", "生态"))
        ]
    return row


def row_to_entries(row: list[str], catalog_name: str, subject_hint: str | None) -> list[dict[str, Any]]:
    joined = " ".join(cell for cell in row if cell)
    if not joined:
        return []
    meta = CATALOG_META[catalog_name]
    issn_match = ISSN_RE.search(joined)
    issn = normalize_issn(issn_match.group(0)) if issn_match else None
    candidates = [clean_title(cell) for cell in title_cells_for_row(row, catalog_name)]
    candidates = [title for title in candidates if not is_noise_title(title)]
    if not candidates:
        candidates = [clean_title(title) for title in JOURNAL_SUFFIX_RE.findall(joined)]
    entries: list[dict[str, Any]] = []
    for title in candidates:
        if is_noise_title(title):
            continue
        entries.append(
            {
                "title_cn": title,
                "issn": issn,
                "subject": subject_hint,
                "catalog": meta["label"],
                "catalog_type": meta["type"],
                "catalog_year": meta["year"],
                "source_file": f"{catalog_name}.pdf",
                "raw_row": row,
            }
        )
    return entries


def parse_catalog(path: Path, catalog_name: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    subject_hint: str | None = None
    for row in rows_from_pdf(path):
        joined = "".join(row)
        if 2 <= len(joined) <= 16 and not ISSN_RE.search(joined) and len(row) <= 2:
            if any(token in joined for token in ("经济", "哲学", "法学", "教育", "医学", "农业", "工程", "数学", "物理", "化学", "管理", "文学", "历史", "社会")):
                subject_hint = joined
        entries.extend(row_to_entries(row, catalog_name, subject_hint))
    return entries


def merge_entries(catalog_entries: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for catalog_name, entries in catalog_entries.items():
        for entry in entries:
            key = normalize_journal_name(entry["title_cn"])
            if not key:
                continue
            current = merged.setdefault(
                key,
                {
                    "title_cn": entry["title_cn"],
                    "issn": entry.get("issn"),
                    "subjects": [],
                    "catalog_labels": [],
                    "catalog_entries": [],
                    "trust_level": "catalog-cn",
                    "evidence": [],
                },
            )
            if entry.get("issn") and not current.get("issn"):
                current["issn"] = entry["issn"]
            if entry.get("subject") and entry["subject"] not in current["subjects"]:
                current["subjects"].append(entry["subject"])
            if entry["catalog"] not in current["catalog_labels"]:
                current["catalog_labels"].append(entry["catalog"])
            current["catalog_entries"].append(entry)
            current["evidence"].append(
                source_evidence(
                    f"{entry['catalog']}-catalog",
                    entry["source_file"],
                    "catalog-cn",
                    tool_tier_used="0",
                )
            )
    for item in merged.values():
        item["updated_at"] = utc_now()
    return sorted(merged.values(), key=lambda item: item["title_cn"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse downloaded Chinese catalog PDFs.")
    parser.add_argument("--data-dir", default=str(Path(__file__).resolve().parents[1] / "data" / "catalogs"))
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    catalog_entries: dict[str, list[dict[str, Any]]] = {}
    for catalog_name in CATALOG_META:
        path = data_dir / f"{catalog_name}.pdf"
        if not path.exists():
            continue
        entries = parse_catalog(path, catalog_name)
        catalog_entries[catalog_name] = entries
        (data_dir / f"{catalog_name}.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{catalog_name}: {len(entries)} entries")
    if not catalog_entries:
        print(f"no catalog PDFs found under {data_dir}", file=sys.stderr)
        return 1
    merged = merge_entries(catalog_entries)
    (data_dir / "merged.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"merged: {len(merged)} entries -> {data_dir / 'merged.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
