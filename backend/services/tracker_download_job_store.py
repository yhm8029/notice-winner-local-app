from __future__ import annotations

import threading
from pathlib import Path
from typing import Any
from uuid import UUID

from backend.api.schemas import TrackerDownloadJobItem

_TRACKER_DOWNLOAD_JOBS_LOCK = threading.Lock()
_TRACKER_DOWNLOAD_JOBS: dict[UUID, dict[str, Any]] = {}
_TRACKER_DOWNLOAD_JOB_ORDER: list[UUID] = []


def store_tracker_download_job(job: dict[str, Any]) -> dict[str, Any]:
    with _TRACKER_DOWNLOAD_JOBS_LOCK:
        _TRACKER_DOWNLOAD_JOBS[job["id"]] = dict(job)
        _TRACKER_DOWNLOAD_JOB_ORDER.insert(0, job["id"])
        del _TRACKER_DOWNLOAD_JOB_ORDER[50:]
        return dict(_TRACKER_DOWNLOAD_JOBS[job["id"]])


def update_tracker_download_job(job_id: UUID, fields: dict[str, Any]) -> dict[str, Any] | None:
    with _TRACKER_DOWNLOAD_JOBS_LOCK:
        existing = _TRACKER_DOWNLOAD_JOBS.get(job_id)
        if existing is None:
            return None
        existing.update(fields)
        _TRACKER_DOWNLOAD_JOBS[job_id] = existing
        return dict(existing)


def get_tracker_download_job(job_id: UUID) -> dict[str, Any] | None:
    with _TRACKER_DOWNLOAD_JOBS_LOCK:
        job = _TRACKER_DOWNLOAD_JOBS.get(job_id)
        return dict(job) if job is not None else None


def find_reusable_tracker_download_job(cache_key: str) -> dict[str, Any] | None:
    with _TRACKER_DOWNLOAD_JOBS_LOCK:
        for job_id in _TRACKER_DOWNLOAD_JOB_ORDER:
            row = _TRACKER_DOWNLOAD_JOBS.get(job_id)
            if row is None or str(row.get("cache_key") or "") != str(cache_key or ""):
                continue
            status = str(row.get("status") or "").strip()
            if status in {"queued", "running"}:
                return dict(row)
            if status == "success":
                output_path = Path(str(row.get("output_path") or ""))
                if output_path.exists():
                    return dict(row)
        return None


def to_tracker_download_job_item(row: dict[str, Any]) -> TrackerDownloadJobItem:
    job_id = UUID(str(row["id"]))
    status = str(row.get("status") or "")
    download_url = (
        f"/api/tracker-entry-summaries/download-jobs/{job_id}/file"
        if status == "success" and str(row.get("output_path") or "").strip()
        else ""
    )
    return TrackerDownloadJobItem(
        id=job_id,
        status=status,
        format=str(row.get("format") or "xlsx"),
        file_name=str(row.get("file_name") or ""),
        download_url=download_url,
        created_at=row["created_at"],
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
        error=str(row.get("error") or ""),
        reused_existing=bool(row.get("reused_existing")),
        summary=dict(row.get("summary") or {}),
    )
