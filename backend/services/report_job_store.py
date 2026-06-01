from __future__ import annotations

import threading
from typing import Any
from uuid import UUID

from backend.api.schemas import ReportJobItem

_REPORT_JOBS_LOCK = threading.Lock()
_REPORT_JOBS: dict[UUID, dict[str, Any]] = {}
_REPORT_JOB_ORDER: list[UUID] = []


def store_report_job(job: dict[str, Any]) -> dict[str, Any]:
    with _REPORT_JOBS_LOCK:
        _REPORT_JOBS[job["id"]] = dict(job)
        _REPORT_JOB_ORDER.insert(0, job["id"])
        del _REPORT_JOB_ORDER[20:]
        return dict(_REPORT_JOBS[job["id"]])


def update_report_job(job_id: UUID, fields: dict[str, Any]) -> dict[str, Any] | None:
    with _REPORT_JOBS_LOCK:
        existing = _REPORT_JOBS.get(job_id)
        if existing is None:
            return None
        existing.update(fields)
        _REPORT_JOBS[job_id] = existing
        return dict(existing)


def get_report_job(job_id: UUID) -> dict[str, Any] | None:
    with _REPORT_JOBS_LOCK:
        job = _REPORT_JOBS.get(job_id)
        return dict(job) if job is not None else None


def list_report_jobs(*, report_name: str = "", limit: int = 10) -> list[dict[str, Any]]:
    with _REPORT_JOBS_LOCK:
        items: list[dict[str, Any]] = []
        for job_id in _REPORT_JOB_ORDER:
            row = _REPORT_JOBS.get(job_id)
            if row is None:
                continue
            if report_name and str(row.get("report_name")) != report_name:
                continue
            items.append(dict(row))
            if len(items) >= limit:
                break
        return items


def to_report_job_item(row: dict[str, Any]) -> ReportJobItem:
    return ReportJobItem(
        id=UUID(str(row["id"])),
        report_name=str(row["report_name"]),
        status=str(row["status"]),
        output_path=str(row.get("output_path") or ""),
        command=[str(item) for item in list(row.get("command") or [])],
        seed_limit=int(row.get("seed_limit") or 0),
        seed_csv=str(row.get("seed_csv") or ""),
        created_at=row["created_at"],
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
        exit_code=int(row["exit_code"]) if row.get("exit_code") is not None else None,
        summary=dict(row.get("summary") or {}),
        log_excerpt=str(row.get("log_excerpt") or ""),
        error=str(row.get("error") or ""),
    )
