from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_backup_common import write_json


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def normalize_path_for_match(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    while normalized.startswith("./") or normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def artifact_match_candidates(value: str) -> set[str]:
    normalized = normalize_path_for_match(value)
    candidates = {normalized} if normalized else set()
    marker = "output/artifacts/"
    if marker in normalized:
        candidates.add(normalized.replace(marker, "output/runs/", 1))
    return candidates


def reconcile_artifacts(artifacts: list[dict[str, Any]], ec2_files: list[dict[str, Any]]) -> dict[str, Any]:
    file_paths = [(item, normalize_path_for_match(str(item.get("path") or ""))) for item in ec2_files]
    matched: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for artifact in artifacts:
        storage_paths = artifact_match_candidates(str(artifact.get("storage_path") or ""))
        if not storage_paths:
            missing.append({**artifact, "missing_reason": "empty storage_path"})
            continue
        match = next(
            (
                item
                for item, path in file_paths
                if any(path.endswith(storage_path) or storage_path.endswith(path) for storage_path in storage_paths)
            ),
            None,
        )
        if match is None:
            missing.append({**artifact, "missing_reason": "no matching EC2 file path"})
        else:
            matched.append({"artifact": artifact, "file": match})
    return {
        "artifact_count": len(artifacts),
        "ec2_file_count": len(ec2_files),
        "matched_count": len(matched),
        "missing_count": len(missing),
        "matched": matched,
        "missing": missing,
    }


def write_reconciliation_report(output_dir: Path, report: dict[str, Any]) -> None:
    write_json(output_dir / "artifact_reconciliation.json", report)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reconcile Supabase run_artifacts rows with EC2 file inventory.")
    parser.add_argument("--supabase-dir", required=True)
    parser.add_argument("--ec2-dir", required=True)
    parser.add_argument("--output-dir", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    supabase_dir = Path(args.supabase_dir)
    ec2_dir = Path(args.ec2_dir)
    output_dir = Path(args.output_dir) if args.output_dir else supabase_dir
    artifacts = read_jsonl(supabase_dir / "tables" / "run_artifacts.jsonl")
    ec2_files = read_jsonl(ec2_dir / "files.jsonl")
    report = reconcile_artifacts(artifacts, ec2_files)
    write_reconciliation_report(output_dir, report)
    print(f"Artifacts matched: {report['matched_count']} / {report['artifact_count']}")
    if report["missing_count"]:
        print(f"Missing artifacts: {report['missing_count']}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
