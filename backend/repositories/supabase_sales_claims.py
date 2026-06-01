from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from backend.sales_claims import append_sales_note_entry
from backend.sales_claims import build_close_sales_note_text
from backend.sales_claims import build_system_sales_note_text
from backend.sales_claims import infer_sales_claim_state_from_note
from backend.sales_claims import normalize_sales_claim_status
from backend.sales_claims import SalesActor
from backend.sales_claims import SALES_CLAIM_STATUS_ACTIVE
from backend.sales_claims import SALES_CLAIM_STATUS_LOST
from backend.sales_claims import SALES_CLAIM_STATUS_WON
from backend.sales_claims import SalesClaimConflictError
from backend.sales_claims import SalesClaimInvalidTransitionError
from backend.sales_claims import SalesClaimNotFoundError
from backend.sales_claims import SalesClaimPermissionError
from backend.sales_claims import SalesClaimRecord
from backend.sales_claims import summarize_sales_claim_records

from .sales_claims import SalesClaimRepository
from .sales_claims import SalesClaimRepositoryConfigError
from .sales_claims import SalesClaimRepositoryError
from .supabase_sales_claims_runtime import build_amount_probe as _build_amount_probe
from .supabase_sales_claims_runtime import is_active_claim_conflict_error as _is_active_claim_conflict_error
from .supabase_sales_claims_runtime import is_missing_column_error as _is_missing_column_error
from .supabase_sales_claims_runtime import normalize_iso_datetime_literal as _normalize_iso_datetime_literal
from .supabase_sales_claims_runtime import parse_datetime as _parse_datetime
from .supabase_sales_claims_runtime import parse_datetime_nullable as _parse_datetime_nullable
from .supabase_sales_claims_runtime import parse_high_krw as _parse_high_krw
from .supabase_sales_claims_runtime import parse_int_nullable as _parse_int_nullable
from .supabase_sales_claims_runtime import parse_low_krw as _parse_low_krw
from .supabase_sales_claims_runtime import parse_uuid as _parse_uuid
from .supabase_sales_claims_runtime import SALES_CLAIM_OVERVIEW_SELECT
from .supabase_sales_claims_runtime import SALES_CLAIM_OVERVIEW_SELECT_FALLBACK
from .supabase_sales_claims_runtime import SALES_CLAIM_SELECT
from .supabase_sales_claims_runtime import SALES_CLAIM_SELECT_FALLBACK
from .supabase_sales_claims_runtime import serialize_claim_snapshot as _serialize_claim_snapshot
from .supabase_http import request_json


@dataclass(frozen=True)
class SupabaseSalesClaimRepositoryConfig:
    base_url: str
    api_key: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseSalesClaimRepositoryConfig":
        base_url = os.getenv("SUPABASE_URL", "").strip()
        api_key = (
            os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET", "").strip()
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_ANON_KEY", "").strip()
        )
        if not base_url:
            raise SalesClaimRepositoryConfigError("SUPABASE_URL is required")
        if not api_key:
            raise SalesClaimRepositoryConfigError(
                "SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET, or SUPABASE_ANON_KEY is required"
            )

        raw_timeout = os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "").strip()
        timeout_seconds = 10.0
        if raw_timeout:
            try:
                timeout_seconds = float(raw_timeout)
            except ValueError as exc:
                raise SalesClaimRepositoryConfigError("SUPABASE_HTTP_TIMEOUT_SECONDS must be numeric") from exc

        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )


class SupabaseSalesClaimRepository(SalesClaimRepository):
    def __init__(self, config: SupabaseSalesClaimRepositoryConfig) -> None:
        self._config = config
        self._rest_url = f"{config.base_url}/rest/v1"

    def list_claims(
        self,
        *,
        organization_id: UUID,
        project_ids: list[UUID] | None = None,
        lightweight: bool = False,
    ) -> list[SalesClaimRecord]:
        query: list[tuple[str, str]] = [
            ("organization_id", f"eq.{organization_id}"),
            ("is_active", "is.true"),
            ("order", "claimed_at.asc"),
        ]
        if project_ids:
            joined = ",".join(str(item) for item in project_ids)
            query.append(("project_id", f"in.({joined})"))
        rows, _headers = self._query_claim_rows(query=query, lightweight=lightweight)
        return [self._normalize_claim_row(row) for row in list(rows or [])]

    def claim_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        source_entry_id: UUID | None,
        source_run_id: UUID | None,
        project_name: str,
        estimated_amount_text: str,
    ) -> tuple[bool, SalesClaimRecord]:
        existing = self._get_active_claim(
            organization_id=actor.organization_id,
            project_id=project_id,
        )
        if existing is not None:
            if actor.user_id is not None and existing.owner_user_id == actor.user_id:
                return False, existing
            raise SalesClaimConflictError(existing)

        now = datetime.now(timezone.utc)
        payload = {
            "organization_id": str(actor.organization_id),
            "project_id": str(project_id),
            "source_entry_id": str(source_entry_id) if source_entry_id else None,
            "source_run_id": str(source_run_id) if source_run_id else None,
            "project_name": str(project_name or ""),
            "owner_user_id": str(actor.user_id) if actor.user_id else None,
            "owner_email": str(actor.email or ""),
            "owner_display_name": str(actor.display_name or actor.email or ""),
            "claimed_at": now.isoformat(),
            "current_owner_assigned_at": now.isoformat(),
            "claim_status": SALES_CLAIM_STATUS_ACTIVE,
            "sales_note": "",
            "estimated_amount_text": str(estimated_amount_text or ""),
            "estimated_amount_low_krw": _parse_low_krw(estimated_amount_text),
            "estimated_amount_high_krw": _parse_high_krw(estimated_amount_text),
        }

        try:
            rows, _headers = self._request_json(
                method="POST",
                path="/project_sales_claims",
                headers={"Prefer": "return=representation"},
                payload=payload,
            )
        except SalesClaimRepositoryError as exc:
            message = str(exc)
            if _is_missing_column_error(message, "current_owner_assigned_at") or _is_missing_column_error(
                message, "claim_status"
            ):
                fallback_payload = dict(payload)
                fallback_payload.pop("current_owner_assigned_at", None)
                fallback_payload.pop("claim_status", None)
                rows, _headers = self._request_json(
                    method="POST",
                    path="/project_sales_claims",
                    headers={"Prefer": "return=representation"},
                    payload=fallback_payload,
                )
            elif _is_active_claim_conflict_error(message):
                existing = self._get_active_claim(
                    organization_id=actor.organization_id,
                    project_id=project_id,
                )
                if existing is not None:
                    if actor.user_id is not None and existing.owner_user_id == actor.user_id:
                        return False, existing
                    raise SalesClaimConflictError(existing) from exc
                raise
            else:
                raise

        if not rows:
            raise SalesClaimRepositoryError("Supabase did not return the created sales claim row")

        claim = self._normalize_claim_row(rows[0])
        self._create_event(
            claim_id=self._extract_claim_id(rows[0]),
            organization_id=actor.organization_id,
            project_id=project_id,
            actor=actor,
            event_type="claim",
            old_value_json={},
            new_value_json=_serialize_claim_snapshot(claim),
        )
        return True, claim

    def update_sales_note(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        sales_note: str,
        force_admin_override: bool = False,
    ) -> SalesClaimRecord:
        existing = self._get_active_claim(
            organization_id=actor.organization_id,
            project_id=project_id,
        )
        if existing is None:
            raise SalesClaimNotFoundError("sales claim not found")
        owner_match = actor.user_id is not None and existing.owner_user_id == actor.user_id
        if not owner_match and not (force_admin_override and actor.is_admin):
            raise SalesClaimPermissionError("only the claim owner can update sales_note")
        if existing.claim_status != SALES_CLAIM_STATUS_ACTIVE and not (force_admin_override and actor.is_admin):
            raise SalesClaimInvalidTransitionError("closed sales claims cannot be updated")

        now = datetime.now(timezone.utc)
        rows, _headers = self._request_json(
            method="PATCH",
            path="/project_sales_claims",
            query=[
                ("id", f"eq.{self._get_active_claim_row_id(actor.organization_id, project_id)}"),
                ("organization_id", f"eq.{actor.organization_id}"),
            ],
            headers={"Prefer": "return=representation"},
            payload={
                "sales_note": str(sales_note or ""),
                "sales_note_updated_at": now.isoformat(),
                "sales_note_updated_by": str(actor.user_id) if actor.user_id else None,
            },
        )
        if not rows:
            raise SalesClaimRepositoryError("Supabase did not return the updated sales claim row")
        claim = self._normalize_claim_row(rows[0])
        self._create_event(
            claim_id=self._extract_claim_id(rows[0]),
            organization_id=actor.organization_id,
            project_id=project_id,
            actor=actor,
            event_type="note_update",
            old_value_json={"sales_note": existing.sales_note},
            new_value_json={"sales_note": claim.sales_note},
        )
        return claim

    def transfer_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        target_user_id: UUID | None,
        target_email: str,
        target_display_name: str,
        force: bool = False,
    ) -> SalesClaimRecord:
        existing = self._get_active_claim(
            organization_id=actor.organization_id,
            project_id=project_id,
        )
        if existing is None:
            raise SalesClaimNotFoundError("sales claim not found")
        owner_match = actor.user_id is not None and existing.owner_user_id == actor.user_id
        if not owner_match and not (force and actor.is_admin):
            raise SalesClaimPermissionError("you do not have permission to transfer this claim")
        if existing.claim_status != SALES_CLAIM_STATUS_ACTIVE:
            raise SalesClaimInvalidTransitionError("closed sales claims cannot be transferred")

        next_owner_email = str(target_email or "").strip().lower()
        if not next_owner_email:
            raise SalesClaimInvalidTransitionError("target user is required")
        if target_user_id is not None and existing.owner_user_id == target_user_id:
            raise SalesClaimInvalidTransitionError("claim is already assigned to that user")
        if next_owner_email == existing.owner_email.strip().lower():
            raise SalesClaimInvalidTransitionError("claim is already assigned to that user")

        now = datetime.now(timezone.utc)
        next_sales_note = append_sales_note_entry(
            existing.sales_note,
            build_system_sales_note_text(
                f"{existing.owner_display_name or existing.owner_email} -> "
                f"{target_display_name or next_owner_email} 이관"
            ),
            timestamp=now,
        )
        row_id = self._get_active_claim_row_id(actor.organization_id, project_id)
        payload = {
            "owner_user_id": str(target_user_id) if target_user_id else None,
            "owner_email": next_owner_email,
            "owner_display_name": str(target_display_name or next_owner_email),
            "current_owner_assigned_at": now.isoformat(),
            "sales_note": next_sales_note,
            "sales_note_updated_at": now.isoformat(),
            "sales_note_updated_by": str(actor.user_id) if actor.user_id else None,
        }
        try:
            rows, _headers = self._request_json(
                method="PATCH",
                path="/project_sales_claims",
                query=[
                    ("id", f"eq.{row_id}"),
                    ("organization_id", f"eq.{actor.organization_id}"),
                ],
                headers={"Prefer": "return=representation"},
                payload=payload,
            )
        except SalesClaimRepositoryError as exc:
            if _is_missing_column_error(str(exc), "current_owner_assigned_at"):
                fallback_payload = dict(payload)
                fallback_payload.pop("current_owner_assigned_at", None)
                rows, _headers = self._request_json(
                    method="PATCH",
                    path="/project_sales_claims",
                    query=[
                        ("id", f"eq.{row_id}"),
                        ("organization_id", f"eq.{actor.organization_id}"),
                    ],
                    headers={"Prefer": "return=representation"},
                    payload=fallback_payload,
                )
            else:
                raise
        if not rows:
            raise SalesClaimRepositoryError("Supabase did not return the transferred sales claim row")

        claim = self._normalize_claim_row(rows[0])
        self._create_event(
            claim_id=self._extract_claim_id(rows[0]),
            organization_id=actor.organization_id,
            project_id=project_id,
            actor=actor,
            event_type="transfer",
            old_value_json={
                "owner_user_id": str(existing.owner_user_id) if existing.owner_user_id else None,
                "owner_email": existing.owner_email,
                "owner_display_name": existing.owner_display_name,
            },
            new_value_json={
                "owner_user_id": str(claim.owner_user_id) if claim.owner_user_id else None,
                "owner_email": claim.owner_email,
                "owner_display_name": claim.owner_display_name,
                "current_owner_assigned_at": claim.current_owner_assigned_at.isoformat(),
            },
        )
        return claim

    def close_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        outcome: str,
        contract_amount_text: str = "",
        force: bool = False,
    ) -> SalesClaimRecord:
        existing = self._get_active_claim(
            organization_id=actor.organization_id,
            project_id=project_id,
        )
        if existing is None:
            raise SalesClaimNotFoundError("sales claim not found")
        owner_match = actor.user_id is not None and existing.owner_user_id == actor.user_id
        if not owner_match and not (force and actor.is_admin):
            raise SalesClaimPermissionError("you do not have permission to close this claim")
        if existing.claim_status != SALES_CLAIM_STATUS_ACTIVE:
            raise SalesClaimInvalidTransitionError("sales claim is already closed")

        normalized_outcome = normalize_sales_claim_status(outcome)
        if normalized_outcome not in {SALES_CLAIM_STATUS_WON, SALES_CLAIM_STATUS_LOST}:
            raise SalesClaimInvalidTransitionError("sales claim close outcome must be won or lost")

        now = datetime.now(timezone.utc)
        next_sales_note = append_sales_note_entry(
            existing.sales_note,
            build_close_sales_note_text(normalized_outcome, contract_amount_text),
            timestamp=now,
        )
        row_id = self._get_active_claim_row_id(actor.organization_id, project_id)
        payload = {
            "claim_status": normalized_outcome,
            "closed_at": now.isoformat(),
            "closed_by": str(actor.user_id) if actor.user_id else None,
            "sales_note": next_sales_note,
            "sales_note_updated_at": now.isoformat(),
            "sales_note_updated_by": str(actor.user_id) if actor.user_id else None,
        }
        try:
            rows, _headers = self._request_json(
                method="PATCH",
                path="/project_sales_claims",
                query=[
                    ("id", f"eq.{row_id}"),
                    ("organization_id", f"eq.{actor.organization_id}"),
                ],
                headers={"Prefer": "return=representation"},
                payload=payload,
            )
        except SalesClaimRepositoryError as exc:
            if _is_missing_column_error(str(exc), "claim_status") or _is_missing_column_error(str(exc), "closed_at"):
                fallback_payload = dict(payload)
                fallback_payload.pop("claim_status", None)
                fallback_payload.pop("closed_at", None)
                fallback_payload.pop("closed_by", None)
                rows, _headers = self._request_json(
                    method="PATCH",
                    path="/project_sales_claims",
                    query=[
                        ("id", f"eq.{row_id}"),
                        ("organization_id", f"eq.{actor.organization_id}"),
                    ],
                    headers={"Prefer": "return=representation"},
                    payload=fallback_payload,
                )
            else:
                raise
        if not rows:
            raise SalesClaimRepositoryError("Supabase did not return the closed sales claim row")

        claim = self._normalize_claim_row(rows[0])
        self._create_event(
            claim_id=self._extract_claim_id(rows[0]),
            organization_id=actor.organization_id,
            project_id=project_id,
            actor=actor,
            event_type="close_won" if normalized_outcome == SALES_CLAIM_STATUS_WON else "close_lost",
            old_value_json={
                "claim_status": existing.claim_status,
                "closed_at": existing.closed_at.isoformat() if existing.closed_at else None,
            },
            new_value_json={
                "claim_status": claim.claim_status,
                "closed_at": claim.closed_at.isoformat() if claim.closed_at else None,
            },
        )
        return claim

    def release_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        force: bool = False,
    ) -> SalesClaimRecord:
        existing = self._get_active_claim(
            organization_id=actor.organization_id,
            project_id=project_id,
        )
        if existing is None:
            raise SalesClaimNotFoundError("sales claim not found")
        owner_match = actor.user_id is not None and existing.owner_user_id == actor.user_id
        if not owner_match and not (force and actor.is_admin):
            raise SalesClaimPermissionError("you do not have permission to release this claim")

        now = datetime.now(timezone.utc)
        row_id = self._get_active_claim_row_id(actor.organization_id, project_id)
        rows, _headers = self._request_json(
            method="PATCH",
            path="/project_sales_claims",
            query=[
                ("id", f"eq.{row_id}"),
                ("organization_id", f"eq.{actor.organization_id}"),
            ],
            headers={"Prefer": "return=representation"},
            payload={
                "is_active": False,
                "released_at": now.isoformat(),
            },
        )
        if not rows:
            raise SalesClaimRepositoryError("Supabase did not return the released sales claim row")
        claim = self._normalize_claim_row(rows[0])
        self._create_event(
            claim_id=self._extract_claim_id(rows[0]),
            organization_id=actor.organization_id,
            project_id=project_id,
            actor=actor,
            event_type="force_release" if force and actor.is_admin and not owner_match else "release",
            old_value_json=_serialize_claim_snapshot(existing),
            new_value_json=_serialize_claim_snapshot(claim),
        )
        return claim

    def summarize_by_user(self, *, organization_id: UUID) -> list[dict[str, Any]]:
        return summarize_sales_claim_records(self.list_claims(organization_id=organization_id))

    def _get_active_claim(self, *, organization_id: UUID, project_id: UUID) -> SalesClaimRecord | None:
        rows, _headers = self._query_claim_rows(
            query=[
                ("organization_id", f"eq.{organization_id}"),
                ("project_id", f"eq.{project_id}"),
                ("is_active", "is.true"),
                ("limit", "1"),
            ],
        )
        if not rows:
            return None
        return self._normalize_claim_row(rows[0])

    def _get_active_claim_row_id(self, organization_id: UUID, project_id: UUID) -> str:
        rows, _headers = self._request_json(
            method="GET",
            path="/project_sales_claims",
            query=[
                ("select", "id"),
                ("organization_id", f"eq.{organization_id}"),
                ("project_id", f"eq.{project_id}"),
                ("is_active", "is.true"),
                ("limit", "1"),
            ],
        )
        if not rows:
            raise SalesClaimNotFoundError("sales claim not found")
        return str(rows[0].get("id") or "").strip()

    def _create_event(
        self,
        *,
        claim_id: str,
        organization_id: UUID,
        project_id: UUID,
        actor: SalesActor,
        event_type: str,
        old_value_json: dict[str, Any],
        new_value_json: dict[str, Any],
    ) -> None:
        self._request_json(
            method="POST",
            path="/project_sales_claim_events",
            headers={"Prefer": "return=minimal"},
            payload={
                "organization_id": str(organization_id),
                "claim_id": claim_id,
                "project_id": str(project_id),
                "actor_user_id": str(actor.user_id) if actor.user_id else None,
                "actor_email": str(actor.email or ""),
                "actor_display_name": str(actor.display_name or actor.email or ""),
                "event_type": event_type,
                "old_value_json": old_value_json,
                "new_value_json": new_value_json,
            },
        )

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        query: list[tuple[str, str]] | None = None,
        headers: dict[str, str] | None = None,
        payload: dict[str, Any] | list[dict[str, Any]] | None = None,
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
            allow_retry=method.upper() == "POST",
            error_cls=SalesClaimRepositoryError,
        )

    def _query_claim_rows(
        self,
        *,
        query: list[tuple[str, str]],
        lightweight: bool = False,
    ) -> tuple[list[dict[str, Any]] | dict[str, Any], dict[str, str]]:
        select_variants = (
            (SALES_CLAIM_OVERVIEW_SELECT, SALES_CLAIM_OVERVIEW_SELECT_FALLBACK)
            if lightweight
            else (SALES_CLAIM_SELECT, SALES_CLAIM_SELECT_FALLBACK)
        )
        for select_columns in select_variants:
            try:
                return self._request_json(
                    method="GET",
                    path="/project_sales_claims",
                    query=[("select", select_columns), *query],
                )
            except SalesClaimRepositoryError as exc:
                if _is_missing_column_error(str(exc), "current_owner_assigned_at"):
                    continue
                raise
        raise SalesClaimRepositoryError("Supabase sales claim query failed")

    @staticmethod
    def _normalize_claim_row(row: dict[str, Any]) -> SalesClaimRecord:
        claimed_at = _parse_datetime(row.get("claimed_at"))
        inferred_assigned_at, inferred_status, inferred_closed_at = infer_sales_claim_state_from_note(
            str(row.get("sales_note") or ""),
            claimed_at=claimed_at,
        )
        current_owner_assigned_at = _parse_datetime_nullable(row.get("current_owner_assigned_at")) or inferred_assigned_at
        claim_status = normalize_sales_claim_status(row.get("claim_status")) or inferred_status
        if claim_status == SALES_CLAIM_STATUS_ACTIVE and inferred_status != SALES_CLAIM_STATUS_ACTIVE:
            claim_status = inferred_status
        closed_at = _parse_datetime_nullable(row.get("closed_at")) or inferred_closed_at
        return SalesClaimRecord(
            organization_id=UUID(str(row.get("organization_id"))),
            project_id=UUID(str(row.get("project_id"))),
            source_entry_id=_parse_uuid(row.get("source_entry_id")),
            source_run_id=_parse_uuid(row.get("source_run_id")),
            project_name=str(row.get("project_name") or ""),
            owner_user_id=_parse_uuid(row.get("owner_user_id")),
            owner_email=str(row.get("owner_email") or ""),
            owner_display_name=str(row.get("owner_display_name") or ""),
            claimed_at=claimed_at,
            current_owner_assigned_at=current_owner_assigned_at,
            released_at=_parse_datetime_nullable(row.get("released_at")),
            is_active=bool(row.get("is_active")),
            claim_status=claim_status,
            closed_at=closed_at,
            closed_by=_parse_uuid(row.get("closed_by")),
            sales_note=str(row.get("sales_note") or ""),
            sales_note_updated_at=_parse_datetime_nullable(row.get("sales_note_updated_at")),
            sales_note_updated_by=_parse_uuid(row.get("sales_note_updated_by")),
            estimated_amount_text=str(row.get("estimated_amount_text") or ""),
            estimated_amount_low_krw=_parse_int_nullable(row.get("estimated_amount_low_krw")),
            estimated_amount_high_krw=_parse_int_nullable(row.get("estimated_amount_high_krw")),
            created_at=_parse_datetime(row.get("created_at")),
            updated_at=_parse_datetime(row.get("updated_at")),
        )

    @staticmethod
    def _extract_claim_id(row: dict[str, Any]) -> str:
        raw = str(row.get("id") or "").strip()
        if not raw:
            raise SalesClaimRepositoryError("Supabase sales claim row did not include id")
        return raw

