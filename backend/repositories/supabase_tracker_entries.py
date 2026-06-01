from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from backend.phase1_defaults import load_phase1_identity

from . import supabase_tracker_entries_runtime as tracker_runtime
from .tracker_entries import TRACKER_CHANGE_SOURCES
from .tracker_entries import TRACKER_EDITABLE_FIELDS
from .tracker_entries import TrackerEntryPatchResult
from .tracker_entries import TrackerEntryRepository
from .tracker_entries import TrackerEntryRepositoryConfigError
from .tracker_entries import TrackerEntryRepositoryError
from .tracker_entries import TrackerEntryRow
from .tracker_entries import coerce_tracker_override_value
from .supabase_http import request_json

TRACKER_ENTRY_SELECT = tracker_runtime.TRACKER_ENTRY_SELECT
TRACKER_ENTRY_SUMMARY_SELECT = tracker_runtime.TRACKER_ENTRY_SUMMARY_SELECT
TRACKER_ENTRY_EXPORT_SELECT = tracker_runtime.TRACKER_ENTRY_EXPORT_SELECT
TRACKER_EFFECTIVE_EXTENDED_FIELDS = tracker_runtime.TRACKER_EFFECTIVE_EXTENDED_FIELDS
TRACKER_SOURCE_EXTENDED_FIELDS = tracker_runtime.TRACKER_SOURCE_EXTENDED_FIELDS
TRACKER_ENTRY_SELECT_LEGACY = tracker_runtime.TRACKER_ENTRY_SELECT_LEGACY
TRACKER_ENTRY_SUMMARY_SELECT_LEGACY = tracker_runtime.TRACKER_ENTRY_SUMMARY_SELECT_LEGACY
TRACKER_ENTRY_EXPORT_SELECT_LEGACY = tracker_runtime.TRACKER_ENTRY_EXPORT_SELECT_LEGACY
TRACKER_AUDIT_LOG_SELECT = tracker_runtime.TRACKER_AUDIT_LOG_SELECT
TRACKER_PROJECT_NAME_SEARCH_FIELD = tracker_runtime.TRACKER_PROJECT_NAME_SEARCH_FIELD

@dataclass(frozen=True)
class SupabaseTrackerEntryRepositoryConfig:
    base_url: str
    api_key: str
    organization_id: UUID
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseTrackerEntryRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise TrackerEntryRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise TrackerEntryRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )

        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise TrackerEntryRepositoryConfigError(
                    "SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric"
                ) from exc

        identity = load_phase1_identity()
        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            organization_id=identity.organization_id,
            timeout_seconds=timeout_seconds,
        )


class SupabaseTrackerEntryRepository(TrackerEntryRepository):
    def __init__(self, config: SupabaseTrackerEntryRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"
        self._supports_effective_extended_fields: bool = True
        self._supports_source_extended_fields: bool = True

    def list_entry_summaries(
        self,
        *,
        page: int,
        page_size: int,
        q: str,
        region: str,
        exclude_auxiliary_titles: bool,
        edited_only: bool,
        source_run_id: UUID | None,
        source_tracker_run_id: UUID | None,
        sheet_name: str,
        section_name: str,
    ) -> tuple[list[TrackerEntryRow], int]:
        return self._list_entries_with_select(
            select_clause=TRACKER_ENTRY_SUMMARY_SELECT,
            prefer_exact_count=True,
            page=page,
            page_size=page_size,
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )

    def list_entries(
        self,
        *,
        page: int,
        page_size: int,
        q: str,
        region: str,
        exclude_auxiliary_titles: bool,
        edited_only: bool,
        source_run_id: UUID | None,
        source_tracker_run_id: UUID | None,
        sheet_name: str,
        section_name: str,
        ) -> tuple[list[TrackerEntryRow], int]:
        return self._list_entries_with_select(
            select_clause=TRACKER_ENTRY_SELECT,
            prefer_exact_count=False,
            page=page,
            page_size=page_size,
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )

    def list_entries_for_export(
        self,
        *,
        page: int,
        page_size: int,
        q: str,
        region: str,
        exclude_auxiliary_titles: bool,
        edited_only: bool,
        source_run_id: UUID | None,
        source_tracker_run_id: UUID | None,
        sheet_name: str,
        section_name: str,
        ) -> tuple[list[TrackerEntryRow], int]:
        return self._list_entries_with_select(
            select_clause=TRACKER_ENTRY_EXPORT_SELECT,
            prefer_exact_count=False,
            page=page,
            page_size=page_size,
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )

    def get_entries_data_version(self) -> str:
        rows, headers = self._request_json(
            method="GET",
            path="/tracker_entries_effective",
            query=[
                ("select", "id,updated_at"),
                ("organization_id", f"eq.{self._config.organization_id}"),
                ("order", "updated_at.desc"),
                ("limit", "1"),
            ],
            headers={"Prefer": "count=exact"},
        )
        total = self._parse_total_count(headers, fallback=len(rows))
        latest_updated_at = ""
        if isinstance(rows, list) and rows:
            latest_updated_at = str(rows[0].get("updated_at") or "")
        return f"count={total};updated_at={latest_updated_at}"

    def get_entry_by_entry_key(self, entry_key: str) -> TrackerEntryRow | None:
        normalized_key = str(entry_key or "").strip()
        if not normalized_key:
            return None
        query = [
            ("select", self._effective_select_clause(TRACKER_ENTRY_SELECT)),
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("entry_key", f"eq.{normalized_key}"),
            ("limit", "1"),
        ]
        try:
            rows, _headers = request_json(
                rest_url=self._rest_url,
                api_key=self._config.api_key,
                timeout_seconds=self._config.timeout_seconds,
                method="GET",
                path="/tracker_entries_effective",
                query=query,
                error_cls=TrackerEntryRepositoryError,
            )
        except TrackerEntryRepositoryError as exc:
            if not self._supports_effective_extended_fields or not self._is_missing_extended_column_error(str(exc)):
                raise
            self._supports_effective_extended_fields = False
            rows, _headers = request_json(
                rest_url=self._rest_url,
                api_key=self._config.api_key,
                timeout_seconds=self._config.timeout_seconds,
                method="GET",
                path="/tracker_entries_effective",
                query=self._replace_select_clause(query, TRACKER_ENTRY_SELECT_LEGACY),
                error_cls=TrackerEntryRepositoryError,
            )
        if not rows:
            return None
        return self._normalize_entry(dict(rows[0]))

    def _list_entries_with_select(
        self,
        *,
        select_clause: str,
        prefer_exact_count: bool,
        page: int,
        page_size: int,
        q: str,
        region: str,
        exclude_auxiliary_titles: bool,
        edited_only: bool,
        source_run_id: UUID | None,
        source_tracker_run_id: UUID | None,
        sheet_name: str,
        section_name: str,
    ) -> tuple[list[TrackerEntryRow], int]:
        is_global_scope = (
            source_run_id is None
            and source_tracker_run_id is None
            and not sheet_name.strip()
            and not section_name.strip()
        )
        query: list[tuple[str, str]] = [
            ("select", self._effective_select_clause(select_clause)),
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("limit", str(page_size)),
            ("offset", str((page - 1) * page_size)),
        ]
        if is_global_scope:
            # Global project status uses the most recent tracker rows across runs.
            # Order by updated_at so Supabase can use the org+updated_at index.
            query.append(("order", "updated_at.desc"))
            query.append(("order", "id.asc"))
        else:
            query.append(("order", "row_no.asc"))
            query.append(("order", "id.asc"))
        if edited_only:
            query.append(("has_overrides", "is.true"))
        if source_run_id is not None:
            query.append(("source_run_id", f"eq.{source_run_id}"))
        if source_tracker_run_id is not None:
            query.append(("source_tracker_run_id", f"eq.{source_tracker_run_id}"))
        if sheet_name.strip():
            query.append(("sheet_name", f"eq.{sheet_name.strip()}"))
        if section_name.strip():
            query.append(("section_name", f"eq.{section_name.strip()}"))
        if q.strip():
            search_term = self._sanitize_ilike_term(q)
            if search_term:
                query.append(
                    (
                        TRACKER_PROJECT_NAME_SEARCH_FIELD,
                        f"ilike.*{search_term}*",
                    )
                )
        region_clause = self._build_region_or_clause(region)
        if region_clause:
            query.append(("or", region_clause))
        exclude_titles_clause = self._build_exclude_auxiliary_titles_clause(exclude_auxiliary_titles)
        if exclude_titles_clause:
            query.append(("and", exclude_titles_clause))

        headers_arg = {"Prefer": f"count={'exact' if prefer_exact_count or not is_global_scope else 'planned'}"}
        rows: list[dict[str, Any]] | dict[str, Any]
        headers: dict[str, str]
        try:
            rows, headers = self._request_json(
                method="GET",
                path="/tracker_entries_effective",
                query=query,
                headers=headers_arg,
            )
        except TrackerEntryRepositoryError as exc:
            legacy_select = self._legacy_select_clause(select_clause)
            if not self._supports_effective_extended_fields or not legacy_select or not self._is_missing_extended_column_error(str(exc)):
                raise
            self._supports_effective_extended_fields = False
            legacy_query = self._replace_select_clause(query, legacy_select)
            rows, headers = self._request_json(
                method="GET",
                path="/tracker_entries_effective",
                query=legacy_query,
                headers=headers_arg,
            )
        total = self._parse_total_count(headers, fallback=len(rows))
        return [
            self._normalize_entry(row)
            for row in rows
        ], total

    def get_entry(self, entry_id: UUID) -> TrackerEntryRow | None:
        query = [
            ("select", self._effective_select_clause(TRACKER_ENTRY_SELECT)),
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("id", f"eq.{entry_id}"),
            ("limit", "1"),
        ]
        try:
            rows, _headers = self._request_json(
                method="GET",
                path="/tracker_entries_effective",
                query=query,
            )
        except TrackerEntryRepositoryError as exc:
            if not self._supports_effective_extended_fields or not self._is_missing_extended_column_error(str(exc)):
                raise
            self._supports_effective_extended_fields = False
            rows, _headers = self._request_json(
                method="GET",
                path="/tracker_entries_effective",
                query=self._replace_select_clause(query, TRACKER_ENTRY_SELECT_LEGACY),
            )
        if not rows:
            return None
        return self._normalize_entry(rows[0])

    def apply_override(
        self,
        *,
        entry_id: UUID,
        field_name: str,
        new_value: str | None,
        actor_user_id: UUID | None,
        actor_label: str,
        change_source: str,
    ) -> TrackerEntryPatchResult | None:
        if field_name not in TRACKER_EDITABLE_FIELDS:
            raise ValueError(f"unsupported field_name: {field_name}")
        if actor_user_id is None and not actor_label:
            raise ValueError("actor_user_id or actor_label is required")
        if change_source not in TRACKER_CHANGE_SOURCES:
            raise ValueError(f"unsupported change_source: {change_source}")

        before_entry = self.get_entry(entry_id)
        if before_entry is None:
            return None
        coerced_new_value = coerce_tracker_override_value(
            field_name=field_name,
            new_value=new_value,
            current_effective_value=str(before_entry.get(field_name) or ""),
        )

        before_logs, _ = self.list_audit_logs(entry_id=entry_id, cursor=None, limit=1)
        self._request_json(
            method="POST",
            path="/rpc/apply_tracker_entry_override",
            payload={
                "p_tracker_entry_id": str(entry_id),
                "p_field_name": field_name,
                "p_new_value": coerced_new_value,
                "p_actor_user_id": str(actor_user_id) if actor_user_id is not None else None,
                "p_actor_label": actor_label,
                "p_change_source": change_source,
            },
        )

        updated_entry = self.get_entry(entry_id)
        if updated_entry is None:
            raise TrackerEntryRepositoryError(
                f"tracker_entry disappeared after override: {entry_id}"
            )

        changed = before_entry[field_name] != updated_entry[field_name]
        audit_log = None
        if changed:
            after_logs, _ = self.list_audit_logs(entry_id=entry_id, cursor=None, limit=1)
            if after_logs:
                latest = after_logs[0]
                if not before_logs or latest["id"] != before_logs[0]["id"]:
                    audit_log = latest

        return TrackerEntryPatchResult(
            changed=changed,
            entry=updated_entry,
            audit_log=audit_log,
        )

    def upsert_source_entries(
        self,
        *,
        source_run_id: UUID,
        source_tracker_run_id: UUID,
        entries: list[dict[str, Any]],
    ) -> list[TrackerEntryRow]:
        payloads: list[dict[str, Any]] = []
        for entry in entries:
            payload = {
                "organization_id": str(self._config.organization_id),
                "source_run_id": str(source_run_id),
                "source_tracker_run_id": str(source_tracker_run_id),
                "entry_key": str(entry["entry_key"]),
                "sheet_name": str(entry.get("sheet_name", "Sheet1")),
                "section_name": str(entry.get("section_name", "facility_cost")),
                "row_no": int(entry["row_no"]),
                "source_bid_no": str(entry["source_bid_no"]),
                "source_bid_ord": str(entry["source_bid_ord"]),
                "source_project_name_norm": str(entry["source_project_name_norm"]),
            }
            for field_name in TRACKER_EDITABLE_FIELDS:
                payload[f"{field_name}_source"] = str(entry.get(field_name, "") or "")
            payload["opening_scheduled_date_source"] = str(entry.get("opening_scheduled_date") or "")
            payload["contract_date_source"] = str(entry.get("contract_date") or "")
            payload["construction_duration_days_source"] = str(entry.get("construction_duration_days") or "")
            payload["completion_expected_date_explicit_source"] = str(
                entry.get("completion_expected_date_explicit") or ""
            )
            payload["completion_expected_date_computed_source"] = str(
                entry.get("completion_expected_date_computed") or ""
            )
            payloads.append(payload)

        try:
            self._request_json(
                method="POST",
                path="/tracker_entries",
                query=[("on_conflict", "organization_id,entry_key")],
                headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                payload=payloads,
                allow_retry=True,
            )
        except TrackerEntryRepositoryError as exc:
            if not self._supports_source_extended_fields or not self._is_missing_extended_source_column_error(str(exc)):
                raise
            self._supports_source_extended_fields = False
            legacy_payloads = [
                {
                    key: value
                    for key, value in payload.items()
                    if key not in TRACKER_SOURCE_EXTENDED_FIELDS
                }
                for payload in payloads
            ]
            self._request_json(
                method="POST",
                path="/tracker_entries",
                query=[("on_conflict", "organization_id,entry_key")],
                headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                payload=legacy_payloads,
                allow_retry=True,
            )

        query = [
            ("select", self._effective_select_clause(TRACKER_ENTRY_SELECT)),
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("source_tracker_run_id", f"eq.{source_tracker_run_id}"),
            ("order", "row_no.asc"),
            ("order", "id.asc"),
        ]
        try:
            rows, _headers = self._request_json(
                method="GET",
                path="/tracker_entries_effective",
                query=query,
            )
        except TrackerEntryRepositoryError as exc:
            if not self._supports_effective_extended_fields or not self._is_missing_extended_column_error(str(exc)):
                raise
            self._supports_effective_extended_fields = False
            rows, _headers = self._request_json(
                method="GET",
                path="/tracker_entries_effective",
                query=self._replace_select_clause(query, TRACKER_ENTRY_SELECT_LEGACY),
            )
        return [self._normalize_entry(row) for row in rows]

    def delete_entries_by_source_tracker_run_id(self, *, source_tracker_run_id: UUID) -> int:
        rows, _headers = self._request_json(
            method="GET",
            path="/tracker_entries",
            query=[
                ("select", "id"),
                ("organization_id", f"eq.{self._config.organization_id}"),
                ("source_tracker_run_id", f"eq.{source_tracker_run_id}"),
            ],
        )
        entry_ids = [str(row.get("id") or "").strip() for row in rows if str(row.get("id") or "").strip()]
        if entry_ids:
            self._request_json(
                method="DELETE",
                path="/tracker_entry_audit_logs",
                query=[
                    ("organization_id", f"eq.{self._config.organization_id}"),
                    ("tracker_entry_id", f"in.({','.join(entry_ids)})"),
                ],
                headers={"Prefer": "return=minimal"},
            )
        deleted_rows, _headers = self._request_json(
            method="DELETE",
            path="/tracker_entries",
            query=[
                ("organization_id", f"eq.{self._config.organization_id}"),
                ("source_tracker_run_id", f"eq.{source_tracker_run_id}"),
            ],
            headers={"Prefer": "return=representation"},
        )
        return len(deleted_rows)

    def list_audit_logs(
        self,
        *,
        entry_id: UUID,
        cursor: int | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int | None]:
        query: list[tuple[str, str]] = [
            ("select", TRACKER_AUDIT_LOG_SELECT),
            ("organization_id", f"eq.{self._config.organization_id}"),
            ("tracker_entry_id", f"eq.{entry_id}"),
            ("order", "id.desc"),
            ("limit", str(limit + 1)),
        ]
        if cursor is not None:
            query.append(("id", f"lt.{cursor}"))

        rows, _headers = self._request_json(
            method="GET",
            path="/tracker_entry_audit_logs",
            query=query,
        )
        page_items = rows[:limit]
        next_cursor = int(page_items[-1]["id"]) if len(rows) > limit and page_items else None
        return [self._normalize_audit_log(row) for row in page_items], next_cursor

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        query: list[tuple[str, str]] | None = None,
        headers: dict[str, str] | None = None,
        payload: dict[str, Any] | list[dict[str, Any]] | None = None,
        allow_retry: bool = False,
    ) -> tuple[list[dict[str, Any]] | dict[str, Any], dict[str, str]]:
        return request_json(
            rest_url=self._rest_url,
            api_key=self._config.api_key,
            timeout_seconds=self._config.timeout_seconds,
            method=method,
            path=path,
            query=query,
            headers=headers,
            payload=payload,
            allow_retry=allow_retry,
            error_cls=TrackerEntryRepositoryError,
        )

    def _normalize_entry(self, row: dict[str, Any]) -> TrackerEntryRow:
        return tracker_runtime.normalize_entry(row)

    def _normalize_audit_log(self, row: dict[str, Any]) -> dict[str, Any]:
        return tracker_runtime.normalize_audit_log(row)

    def _parse_total_count(self, headers: dict[str, str], *, fallback: int) -> int:
        return tracker_runtime.parse_total_count(headers, fallback=fallback)

    def _sanitize_ilike_term(self, value: str) -> str:
        return tracker_runtime.sanitize_ilike_term(value)

    def _build_region_or_clause(self, region: str) -> str:
        return tracker_runtime.build_region_or_clause(region)

    def _build_exclude_auxiliary_titles_clause(self, enabled: bool) -> str:
        return tracker_runtime.build_exclude_auxiliary_titles_clause(enabled)

    def _escape_postgrest_literal(self, value: str) -> str:
        return tracker_runtime.escape_postgrest_literal(value)

    def _effective_select_clause(self, select_clause: str) -> str:
        return tracker_runtime.effective_select_clause(
            select_clause,
            supports_effective_extended_fields=self._supports_effective_extended_fields,
        )

    def _legacy_select_clause(self, select_clause: str) -> str:
        return tracker_runtime.legacy_select_clause(select_clause)

    def _replace_select_clause(
        self,
        query: list[tuple[str, str]],
        select_clause: str,
    ) -> list[tuple[str, str]]:
        return tracker_runtime.replace_select_clause(query, select_clause)

    def _is_missing_extended_column_error(self, message: str) -> bool:
        return tracker_runtime.is_missing_extended_column_error(message)

    def _is_missing_extended_source_column_error(self, message: str) -> bool:
        return tracker_runtime.is_missing_extended_source_column_error(message)
