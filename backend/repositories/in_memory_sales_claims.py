from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.sales_claims import InMemorySalesClaimStore
from backend.sales_claims import SalesActor
from backend.sales_claims import SalesClaimRecord

from .sales_claims import SalesClaimRepository


class InMemorySalesClaimRepository(SalesClaimRepository):
    def __init__(self, store: InMemorySalesClaimStore | None = None) -> None:
        self._store = store or InMemorySalesClaimStore()

    def list_claims(
        self,
        *,
        organization_id: UUID,
        project_ids: list[UUID] | None = None,
        lightweight: bool = False,
    ) -> list[SalesClaimRecord]:
        return self._store.list_claims(organization_id=organization_id, project_ids=project_ids)

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
        return self._store.claim_project(
            actor=actor,
            project_id=project_id,
            source_entry_id=source_entry_id,
            source_run_id=source_run_id,
            project_name=project_name,
            estimated_amount_text=estimated_amount_text,
        )

    def update_sales_note(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        sales_note: str,
        force_admin_override: bool = False,
    ) -> SalesClaimRecord:
        return self._store.update_sales_note(
            actor=actor,
            project_id=project_id,
            sales_note=sales_note,
            force_admin_override=force_admin_override,
        )

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
        return self._store.transfer_project(
            actor=actor,
            project_id=project_id,
            target_user_id=target_user_id,
            target_email=target_email,
            target_display_name=target_display_name,
            force=force,
        )

    def close_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        outcome: str,
        contract_amount_text: str = "",
        force: bool = False,
    ) -> SalesClaimRecord:
        return self._store.close_project(
            actor=actor,
            project_id=project_id,
            outcome=outcome,
            contract_amount_text=contract_amount_text,
            force=force,
        )

    def release_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        force: bool = False,
    ) -> SalesClaimRecord:
        return self._store.release_project(
            actor=actor,
            project_id=project_id,
            force=force,
        )

    def summarize_by_user(self, *, organization_id: UUID) -> list[dict[str, Any]]:
        return self._store.summarize_by_user(organization_id=organization_id)
