from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Request

from backend.api.routers.sales_claims import claim_sales_project as sales_claims_claim_sales_project
from backend.api.routers.sales_claims import close_sales_claim as sales_claims_close_sales_claim
from backend.api.routers.sales_claims import patch_sales_claim as sales_claims_patch_sales_claim
from backend.api.routers.sales_claims import release_sales_claim as sales_claims_release_sales_claim
from backend.api.routers.sales_claims import transfer_sales_claim as sales_claims_transfer_sales_claim
from backend.api.schemas import ErrorResponse
from backend.api.schemas import SalesClaimCloseRequest
from backend.api.schemas import SalesClaimMutationResponse
from backend.api.schemas import SalesClaimPatchRequest
from backend.api.schemas import SalesClaimReleaseRequest
from backend.api.schemas import SalesClaimRequest
from backend.api.schemas import SalesClaimTransferRequest

router = APIRouter()


@router.post(
    "/api/sales-claims/projects/{project_id}/claim",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def claim_sales_project(
    request: Request,
    project_id: UUID,
    payload: SalesClaimRequest,
) -> SalesClaimMutationResponse:
    return sales_claims_claim_sales_project(
        request=request,
        project_id=project_id,
        payload=payload,
    )


@router.patch(
    "/api/sales-claims/projects/{project_id}",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def patch_sales_claim(
    request: Request,
    project_id: UUID,
    payload: SalesClaimPatchRequest,
) -> SalesClaimMutationResponse:
    return sales_claims_patch_sales_claim(
        request=request,
        project_id=project_id,
        payload=payload,
    )


@router.post(
    "/api/sales-claims/projects/{project_id}/transfer",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def transfer_sales_claim(
    request: Request,
    project_id: UUID,
    payload: SalesClaimTransferRequest,
) -> SalesClaimMutationResponse:
    return sales_claims_transfer_sales_claim(
        request=request,
        project_id=project_id,
        payload=payload,
    )


@router.post(
    "/api/sales-claims/projects/{project_id}/close",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def close_sales_claim(
    request: Request,
    project_id: UUID,
    payload: SalesClaimCloseRequest,
) -> SalesClaimMutationResponse:
    return sales_claims_close_sales_claim(
        request=request,
        project_id=project_id,
        payload=payload,
    )


@router.post(
    "/api/sales-claims/projects/{project_id}/release",
    response_model=SalesClaimMutationResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def release_sales_claim(
    request: Request,
    project_id: UUID,
    payload: SalesClaimReleaseRequest,
) -> SalesClaimMutationResponse:
    return sales_claims_release_sales_claim(
        request=request,
        project_id=project_id,
        payload=payload,
    )
