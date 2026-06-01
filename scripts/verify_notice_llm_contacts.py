from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.attachment_text_extract import download_attachment_text
from backend.services.native_gui_rules import extract_contact_from_notice_text
from backend.services.native_gui_rules import extract_notice_area_value
from backend.services.native_gui_rules import extract_notice_cost_won
from backend.services.native_gui_rules import format_won
from backend.services.native_llm_correction import DEFAULT_MODEL
from backend.services.native_llm_correction import LlmCorrectionConfig
from backend.services.native_llm_correction import maybe_correct_notice_fields_with_llm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify rule extraction and live LLM contact correction on notice attachments.")
    parser.add_argument("--bid-no", action="append", required=True, help="Bid number to inspect. Repeat for multiple bids.")
    parser.add_argument(
        "--empty-contact-bid",
        action="append",
        default=[],
        help="Bid number to re-run with an empty contact so the live LLM must infer the contact.",
    )
    parser.add_argument("--anthropic-key", default=(os.getenv("ANTHROPIC_API_KEY") or "").strip())
    parser.add_argument("--llm-model", default=(os.getenv("TRACKER_LLM_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL)
    parser.add_argument("--env-file", default="", help="Optional env file to load if ANTHROPIC_API_KEY is not already set.")
    parser.add_argument("--output", default="", help="Optional JSON report path.")
    return parser.parse_args()


def resolve_api_key(*, explicit_key: str, env_file: str) -> str:
    if str(explicit_key or "").strip():
        return str(explicit_key or "").strip()
    env_key = str(os.getenv("ANTHROPIC_API_KEY") or "").strip()
    if env_key:
        return env_key
    env_path = Path(env_file).expanduser() if env_file else None
    if env_path and env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def find_seed_row(bid_no: str) -> tuple[Path, dict[str, str]]:
    for seed_path in sorted((ROOT / "output" / "artifacts").glob("*/project_tracker_seed_input.csv")):
        with seed_path.open("r", encoding="utf-8-sig", newline="") as fp:
            for row in csv.DictReader(fp):
                if str(row.get("bid_no") or "").strip().upper() == str(bid_no or "").strip().upper():
                    return seed_path, {str(k): str(v or "").strip() for k, v in row.items()}
    raise FileNotFoundError(f"seed row not found for bid_no={bid_no}")


def collect_attachment_docs(row: dict[str, str]) -> list[tuple[str, str]]:
    docs: list[tuple[str, str]] = []
    for index in range(1, 11):
        if index == 1:
            url = str(row.get("spec_doc_url_1") or row.get("spec_doc_url") or "").strip()
            file_name = str(row.get("spec_doc_file_name_1") or row.get("spec_doc_file_name") or "").strip()
        else:
            url = str(row.get(f"spec_doc_url_{index}") or "").strip()
            file_name = str(row.get(f"spec_doc_file_name_{index}") or "").strip()
        if url:
            docs.append((url, file_name))
    return docs


def load_attachment_text(row: dict[str, str], session: requests.Session) -> str:
    parts: list[str] = []
    for url, file_name in collect_attachment_docs(row):
        text = download_attachment_text(url=url, file_name=file_name, session=session)
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def main() -> int:
    args = parse_args()
    api_key = resolve_api_key(explicit_key=args.anthropic_key, env_file=args.env_file)
    if not api_key:
        raise SystemExit("missing ANTHROPIC_API_KEY; pass --anthropic-key or --env-file")

    empty_contact_bids = {str(item or "").strip().upper() for item in args.empty_contact_bid}
    config = LlmCorrectionConfig(
        enabled=True,
        api_key=api_key,
        model=str(args.llm_model or "").strip() or DEFAULT_MODEL,
        max_rows=20,
        max_chars=12000,
    )

    report: list[dict[str, object]] = []
    with requests.Session() as session:
        for bid_no in args.bid_no:
            seed_path, row = find_seed_row(bid_no)
            combined_text = load_attachment_text(row, session)
            project_name = str(row.get("project_name") or "").strip()
            org_name = str(row.get("org_name") or "").strip()
            rule_contact = extract_contact_from_notice_text(combined_text, org_name)
            area = extract_notice_area_value(combined_text, project_name)
            cost = format_won(extract_notice_cost_won(combined_text))

            llm_with_rule_contact = maybe_correct_notice_fields_with_llm(
                config=config,
                text=combined_text,
                project_name=project_name,
                org_name=org_name,
                area=area,
                cost=cost,
                contact=rule_contact,
            )

            llm_with_empty_contact = None
            if str(bid_no or "").strip().upper() in empty_contact_bids:
                empty_result = maybe_correct_notice_fields_with_llm(
                    config=config,
                    text=combined_text,
                    project_name=project_name,
                    org_name=org_name,
                    area=area,
                    cost=cost,
                    contact="",
                )
                llm_with_empty_contact = {
                    "result_contact": empty_result.contact,
                    "corrected_fields": list(empty_result.corrected_fields),
                }

            report.append(
                {
                    "bid_no": str(bid_no or "").strip(),
                    "project_name": project_name,
                    "org_name": org_name,
                    "seed_source": str(seed_path),
                    "rule_contact": rule_contact,
                    "rule_area": area,
                    "rule_cost": cost,
                    "llm_model": config.model,
                    "llm_with_rule_contact": {
                        "result_contact": llm_with_rule_contact.contact,
                        "corrected_fields": list(llm_with_rule_contact.corrected_fields),
                    },
                    "llm_with_empty_contact": llm_with_empty_contact,
                }
            )

    payload = {"items": report}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
