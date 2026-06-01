from __future__ import annotations

import csv
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from pathlib import Path
from typing import Callable


OUTPUT_FIELDNAMES = [
    "bid_no",
    "bid_ord",
    "rank",
    "project_name_norm",
    "g2b_verified",
    "source_type",
    "internal_search_url",
    "post_url",
    "post_title",
    "winner_name",
    "winner_confidence",
    "winner_pattern",
    "post_score",
    "file_url",
    "file_name",
    "confidence_score",
    "reason_code",
    "review_flag",
    "escalate",
    "contract_name",
    "contract_date",
    "notice_construction_cost",
    "notice_construction_cost_source",
    "contract_amount",
    "contract_amount_source",
    "gross_area_scale",
    "gross_area_scale_source",
    "demand_contact",
    "demand_contact_source",
    "client_location",
    "client_location_source",
    "site_location",
    "site_location_source",
    "architect_office",
    "architect_office_source",
    "construction_start_date",
    "construction_start_date_source",
    "construction_duration_days",
    "completion_expected_date_explicit",
    "completion_expected_date_computed",
    "building_automation_estimated_amount",
    "building_automation_estimated_amount_source",
    "evidence_source",
    "parser_version",
    "run_mode",
    "status",
    "hub_check_note",
]


def load_grouped_items(internal_nav_csv: Path) -> list[tuple[tuple[str, str], list[dict[str, str]]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    with internal_nav_csv.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            bid_no = str(row.get("bid_no") or "").strip()
            bid_ord = str(row.get("bid_ord") or "").strip() or "000"
            grouped.setdefault((bid_no, bid_ord), []).append({key: str(value or "") for key, value in row.items()})
    return list(grouped.items())


def write_output_rows(out_csv: Path, out_rows: list[dict[str, str]]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(out_rows)


def process_grouped_items_parallel(
    *,
    grouped_items: list[tuple[tuple[str, str], list[dict[str, str]]]],
    worker_count: int,
    build_output_row_fn: Callable[..., tuple[dict[str, str], str, bool]],
    llm_config: object,
    progress_cb: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
    raise_if_stop_requested_fn: Callable[[Callable[[], bool] | None], None],
) -> list[dict[str, str]]:
    indexed_rows: dict[int, dict[str, str]] = {}
    executor = ThreadPoolExecutor(max_workers=worker_count)
    pending: dict[object, int] = {}
    grouped_iter = iter(enumerate(grouped_items))
    cancelled = False
    try:
        while len(pending) < worker_count:
            raise_if_stop_requested_fn(should_stop)
            try:
                index, group_item = next(grouped_iter)
            except StopIteration:
                break
            pending[
                executor.submit(
                    build_output_row_fn,
                    group_item=group_item,
                    llm_config=llm_config,
                    use_llm=False,
                    should_stop=should_stop,
                )
            ] = index
        while pending:
            raise_if_stop_requested_fn(should_stop)
            done, _not_done = wait(tuple(pending.keys()), return_when=FIRST_COMPLETED)
            for future in done:
                index = pending.pop(future)
                out_row, progress_message, _ = future.result()
                indexed_rows[index] = out_row
                if progress_cb is not None and progress_message:
                    progress_cb(progress_message)
            while len(pending) < worker_count:
                raise_if_stop_requested_fn(should_stop)
                try:
                    index, group_item = next(grouped_iter)
                except StopIteration:
                    break
                pending[
                    executor.submit(
                        build_output_row_fn,
                        group_item=group_item,
                        llm_config=llm_config,
                        use_llm=False,
                        should_stop=should_stop,
                    )
                ] = index
    except InterruptedError:
        cancelled = True
        raise
    finally:
        executor.shutdown(wait=not cancelled, cancel_futures=cancelled)
    return [indexed_rows[index] for index in sorted(indexed_rows)]
