from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env_file(path: str) -> None:
    env_path = Path(path).expanduser()
    if not env_path.is_absolute():
        env_path = ROOT / env_path
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill tracker entry snapshot read models.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--limit", type=int, default=0, help="Optional max rows to process.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(args.env_file)

    from backend.api.app import _upsert_tracker_entry_snapshots_best_effort
    from backend.phase1_defaults import load_phase1_identity
    from backend.repositories import get_tracker_entry_repository
    from backend.repositories import reset_tracker_entry_repository
    from backend.repositories import reset_tracker_entry_snapshot_repository

    reset_tracker_entry_repository()
    reset_tracker_entry_snapshot_repository()

    organization_id = load_phase1_identity().organization_id
    repository = get_tracker_entry_repository()

    page = 1
    processed = 0
    while True:
        rows, _total = repository.list_entries(
            page=page,
            page_size=max(1, int(args.page_size or 200)),
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )
        if not rows:
            break
        if args.limit and processed >= args.limit:
            break
        batch = rows
        if args.limit:
            remaining = max(0, args.limit - processed)
            batch = rows[:remaining]
        _upsert_tracker_entry_snapshots_best_effort(
            organization_id=organization_id,
            rows=[dict(row) for row in batch],
        )
        processed += len(batch)
        print(f"tracker snapshots upserted: {processed}")
        if len(rows) < args.page_size or (args.limit and processed >= args.limit):
            break
        page += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
