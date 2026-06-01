from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.attachment_text_extract import download_attachment_text


@dataclass(frozen=True)
class SeedDoc:
    url: str
    file_name: str


@dataclass(frozen=True)
class SeedRow:
    bid_no: str
    bid_ord: str
    project_name: str
    org_name: str
    sources: tuple[str, ...]
    docs: tuple[SeedDoc, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay historical seed CSV artifacts with cached attachments.")
    parser.add_argument("--old-ref", default="HEAD^")
    parser.add_argument("--new-ref", default="HEAD")
    parser.add_argument(
        "--seed-glob",
        default="output/artifacts/*/project_tracker_seed_input.csv",
        help="Glob for project tracker seed CSV artifacts.",
    )
    parser.add_argument(
        "--cache-dir",
        default="output/cache/historical_seed_replay",
        help="Directory for cached attachment texts.",
    )
    parser.add_argument("--output", default="", help="Optional JSON report path.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit for unique seed rows.")
    return parser.parse_args()


def load_git_module(module_name: str, relative_path: str, git_ref: str) -> types.ModuleType:
    if str(git_ref).strip().upper() == "WORKTREE":
        source = (ROOT / relative_path).read_text(encoding="utf-8").lstrip("\ufeff")
    else:
        source = subprocess.check_output(
            ["git", "show", f"{git_ref}:{relative_path}"],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
        ).lstrip("\ufeff")
    module = types.ModuleType(module_name)
    sys.modules[module_name] = module
    exec(source, module.__dict__)
    return module


def discover_seed_paths(seed_glob: str) -> list[Path]:
    paths = sorted(ROOT.glob(seed_glob))
    return [path.resolve() for path in paths if path.is_file()]


def _doc_from_row(row: dict[str, str], index: int) -> SeedDoc | None:
    if index == 1:
        url = str(row.get("spec_doc_url_1") or row.get("spec_doc_url") or "").strip()
        file_name = str(row.get("spec_doc_file_name_1") or row.get("spec_doc_file_name") or "").strip()
    else:
        url = str(row.get(f"spec_doc_url_{index}") or "").strip()
        file_name = str(row.get(f"spec_doc_file_name_{index}") or "").strip()
    if not url:
        return None
    return SeedDoc(url=url, file_name=file_name)


def collect_unique_seed_rows(seed_paths: list[Path]) -> list[SeedRow]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for seed_path in seed_paths:
        with seed_path.open("r", encoding="utf-8-sig", newline="") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                bid_no = str(row.get("bid_no") or "").strip()
                bid_ord = str(row.get("bid_ord") or "").strip() or "000"
                project_name = str(row.get("project_name") or "").strip()
                org_name = str(row.get("org_name") or "").strip()
                if not bid_no or not project_name:
                    continue
                key = (bid_no.upper(), bid_ord, project_name)
                entry = merged.setdefault(
                    key,
                    {
                        "bid_no": bid_no.upper(),
                        "bid_ord": bid_ord,
                        "project_name": project_name,
                        "org_name": org_name,
                        "sources": set(),
                        "docs": [],
                        "doc_keys": set(),
                    },
                )
                entry["sources"].add(str(seed_path))
                if not entry["org_name"] and org_name:
                    entry["org_name"] = org_name
                for index in range(1, 11):
                    doc = _doc_from_row(row, index)
                    if doc is None:
                        continue
                    doc_key = (doc.url, doc.file_name)
                    if doc_key in entry["doc_keys"]:
                        continue
                    entry["doc_keys"].add(doc_key)
                    entry["docs"].append(doc)
    rows: list[SeedRow] = []
    for entry in merged.values():
        rows.append(
            SeedRow(
                bid_no=str(entry["bid_no"]),
                bid_ord=str(entry["bid_ord"]),
                project_name=str(entry["project_name"]),
                org_name=str(entry["org_name"]),
                sources=tuple(sorted(str(item) for item in entry["sources"])),
                docs=tuple(entry["docs"]),
            )
        )
    rows.sort(key=lambda item: (item.bid_no, item.bid_ord, item.project_name))
    return rows


def cache_file_path(cache_dir: Path, *, url: str, file_name: str) -> Path:
    digest = hashlib.sha256(f"{url}\n{file_name}".encode("utf-8")).hexdigest()
    return cache_dir / digest[:2] / f"{digest}.json"


def load_cached_attachment_text(
    *,
    cache_dir: Path,
    session: requests.Session,
    url: str,
    file_name: str,
    counters: dict[str, int],
) -> str:
    cache_path = cache_file_path(cache_dir, url=url, file_name=file_name)
    if cache_path.exists():
        counters["cache_hits"] += 1
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        return str(payload.get("text") or "")
    counters["cache_misses"] += 1
    text = download_attachment_text(url=url, file_name=file_name, session=session)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"url": url, "file_name": file_name, "text": text}, ensure_ascii=False),
        encoding="utf-8",
    )
    return text


def format_won(value: int) -> str:
    if int(value or 0) <= 0:
        return ""
    return f"{int(value):,}원"


def build_report(*, old_ref: str, new_ref: str, rows: list[SeedRow], cache_dir: Path) -> dict[str, Any]:
    old_gui_rules = load_git_module("historical_old_native_gui_rules", "backend/services/native_gui_rules.py", old_ref)
    new_gui_rules = load_git_module("historical_new_native_gui_rules", "backend/services/native_gui_rules.py", new_ref)
    old_cost_fn = old_gui_rules.extract_notice_cost_won
    old_contact_fn = old_gui_rules.extract_contact_from_notice_text
    new_cost_fn = new_gui_rules.extract_notice_cost_won
    new_contact_fn = new_gui_rules.extract_contact_from_notice_text

    counters = {"cache_hits": 0, "cache_misses": 0}
    changed_cost: list[dict[str, Any]] = []
    changed_contact: list[dict[str, Any]] = []
    unchanged_rows = 0

    with requests.Session() as session:
        for index, row in enumerate(rows, start=1):
            texts: list[str] = []
            for doc in row.docs:
                text = load_cached_attachment_text(
                    cache_dir=cache_dir,
                    session=session,
                    url=doc.url,
                    file_name=doc.file_name,
                    counters=counters,
                )
                if text:
                    texts.append(text)
            combined_text = "\n\n".join(texts)
            old_cost = int(old_cost_fn(combined_text) or 0)
            new_cost = int(new_cost_fn(combined_text) or 0)
            old_contact = str(old_contact_fn(combined_text, row.org_name) or "").strip()
            new_contact = str(new_contact_fn(combined_text, row.org_name) or "").strip()

            if old_cost == new_cost and old_contact == new_contact:
                unchanged_rows += 1
                continue

            base_payload = {
                "bid_no": row.bid_no,
                "bid_ord": row.bid_ord,
                "project_name": row.project_name,
                "org_name": row.org_name,
                "doc_count": len(row.docs),
                "sources": list(row.sources),
                "row_index": index,
            }
            if old_cost != new_cost:
                changed_cost.append(
                    {
                        **base_payload,
                        "old_cost": format_won(old_cost),
                        "new_cost": format_won(new_cost),
                    }
                )
            if old_contact != new_contact:
                changed_contact.append(
                    {
                        **base_payload,
                        "old_contact": old_contact,
                        "new_contact": new_contact,
                        "old_would_need_llm": not bool(old_contact),
                        "new_would_need_llm": _needs_contact_llm_for_report(new_contact),
                    }
                )

    return {
        "old_ref": old_ref,
        "new_ref": new_ref,
        "seed_row_count": len(rows),
        "unchanged_row_count": unchanged_rows,
        "changed_cost_count": len(changed_cost),
        "changed_contact_count": len(changed_contact),
        "cache": counters,
        "changed_cost_rows": changed_cost,
        "changed_contact_rows": changed_contact,
    }


def _needs_contact_llm_for_report(contact: str) -> bool:
    normalized = str(contact or "").strip()
    if not normalized:
        return True
    if "/" not in normalized:
        return True
    dept = str(normalized.split("/", 1)[0] or "").strip()
    dept_norm = "".join(dept.split())
    if not dept_norm:
        return True
    if len(dept_norm) <= 2:
        return True
    if dept_norm in {"부서별자료실"}:
        return True
    return False


def print_summary(report: dict[str, Any]) -> None:
    print(f"refs: {report['old_ref']} -> {report['new_ref']}")
    print(f"seed rows: {report['seed_row_count']}")
    print(f"unchanged rows: {report['unchanged_row_count']}")
    print(f"changed cost rows: {report['changed_cost_count']}")
    print(f"changed contact rows: {report['changed_contact_count']}")
    cache = report["cache"]
    print(f"cache hits: {cache['cache_hits']}")
    print(f"cache misses: {cache['cache_misses']}")
    if report["changed_cost_rows"]:
        print("cost changes:")
        for row in report["changed_cost_rows"]:
            print(
                f"  {row['bid_no']} {row['project_name']} :: {row['old_cost']} -> {row['new_cost']}"
            )
    if report["changed_contact_rows"]:
        print("contact changes:")
        for row in report["changed_contact_rows"]:
            llm_flag = " llm" if row["new_would_need_llm"] else ""
            print(
                f"  {row['bid_no']} {row['project_name']} :: {row['old_contact']} -> {row['new_contact']}{llm_flag}"
            )


def main() -> int:
    args = parse_args()
    seed_paths = discover_seed_paths(args.seed_glob)
    if not seed_paths:
        raise SystemExit(f"no seed csv files matched: {args.seed_glob}")
    rows = collect_unique_seed_rows(seed_paths)
    if args.limit > 0:
        rows = rows[: args.limit]
    cache_dir = (ROOT / args.cache_dir).resolve()
    report = build_report(old_ref=args.old_ref, new_ref=args.new_ref, rows=rows, cache_dir=cache_dir)
    print_summary(report)
    if args.output:
        output_path = (ROOT / args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
