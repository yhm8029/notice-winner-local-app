from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from .native_gui_rules import normalize_contact_candidate
from .native_gui_rules import PHONE_FLEX_PAT


REQUEST_TIMEOUT_SEC = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
ATTACHMENT_FIELD_COUNT = 10
MAX_ATTACHMENT_DOCS = 3
MIN_ATTACHMENT_SCAN_DOCS = 2


def _default_export_row_max_workers(*, getenv_fn: Callable[[str, str], str] | None = None) -> int:
    getenv = getenv_fn or os.getenv
    raw_value = str(getenv("WINNER_PIPELINE_EXPORT_ROW_WORKERS", "12") or "").strip() or "12"
    try:
        return max(1, int(raw_value))
    except ValueError:
        return 12


EXPORT_ROW_MAX_WORKERS = _default_export_row_max_workers()


def _normalize_export_contact_value(value: str, org_name: str) -> str:
    raw = str(value or "").strip()
    if not raw or not PHONE_FLEX_PAT.search(raw):
        return raw
    normalized = normalize_contact_candidate(raw, org_name)
    return normalized or raw


@dataclass(frozen=True)
class PageDocument:
    url: str
    title: str
    text: str


@dataclass(frozen=True)
class AttachmentDocument:
    url: str
    file_name: str
    score: int
    is_announcement_doc: bool
    text: str = ""


@dataclass(frozen=True)
class ExtractedNoticeFields:
    winner_name: str = ""
    winner_pattern: str = ""
    gross_area_scale: str = ""
    construction_cost: str = ""
    demand_contact: str = ""
    client_location: str = ""
    site_location: str = ""
    architect_office: str = ""
    construction_start_date: str = ""
    construction_duration_days: str = ""
    completion_expected_date_explicit: str = ""
    building_automation_estimated_amount: str = ""
    llm_corrected_fields: tuple[str, ...] = ()
    demand_contact_resolution_status: str = ""
    demand_contact_resolution_reason: str = ""
    demand_contact_resolution_phase: str = ""
    demand_contact_resolution_role: str = ""
    demand_contact_resolution_owner_side: str = ""
    demand_contact_resolution_owner_side_basis: str = ""


@dataclass(frozen=True)
class ResolvedField:
    value: str = ""
    source: str = ""


@dataclass(frozen=True)
class AttachmentTextPayload:
    all_text: str = ""
    announcement_text: str = ""
    tried_count: int = 0
    parsed_count: int = 0
    download_ms: int = 0
    parse_ms: int = 0
