from __future__ import annotations

from typing import Any
from typing import Protocol
from uuid import UUID

from backend.sales_claims import SalesActor
from backend.sales_claims import SalesClaimRecord


class SalesClaimRepositoryError(RuntimeError):
    pass


class SalesClaimRepositoryConfigError(SalesClaimRepositoryError):
    pass


class SalesClaimRepository(Protocol):
    def list_claims(
        self,
        *,
        organization_id: UUID,
        project_ids: list[UUID] | None = None,
        lightweight: bool = False,
    ) -> list[SalesClaimRecord]: ...

    def claim_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        source_entry_id: UUID | None,
        source_run_id: UUID | None,
        project_name: str,
        estimated_amount_text: str,
    ) -> tuple[bool, SalesClaimRecord]: ...

    def update_sales_note(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        sales_note: str,
        force_admin_override: bool = False,
    ) -> SalesClaimRecord: ...

    def transfer_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        target_user_id: UUID | None,
        target_email: str,
        target_display_name: str,
        force: bool = False,
    ) -> SalesClaimRecord: ...

    def close_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        outcome: str,
        contract_amount_text: str = "",
        force: bool = False,
    ) -> SalesClaimRecord: ...

    def release_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        force: bool = False,
    ) -> SalesClaimRecord: ...

    def summarize_by_user(self, *, organization_id: UUID) -> list[dict[str, Any]]: ...
