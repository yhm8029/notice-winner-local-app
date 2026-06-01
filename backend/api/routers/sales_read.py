from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi.responses import StreamingResponse

from backend.api.routers.sales_claims import download_sales_claims_workbook as sales_claims_download_sales_claims_workbook
from backend.api.routers.sales_claims import get_sales_claim_overview as sales_claims_get_sales_claim_overview
from backend.api.routers.sales_claims import get_sales_claim_summary_by_user as sales_claims_get_sales_claim_summary_by_user
from backend.api.routers.sales_claims import list_sales_claims as sales_claims_list_sales_claims
from backend.api.routers.tracker import get_home_bootstrap as tracker_get_home_bootstrap
from backend.api.schemas import HomeBootstrapResponse
from backend.api.schemas import SalesClaimListResponse
from backend.api.schemas import SalesClaimOverviewResponse
from backend.api.schemas import SalesClaimSummaryByUserResponse

router = APIRouter()


@router.get(
    "/api/home-bootstrap",
    response_model=HomeBootstrapResponse,
)
def get_home_bootstrap(request: Request) -> HomeBootstrapResponse:
    return tracker_get_home_bootstrap(request)


@router.get(
    "/api/sales-claims",
    response_model=SalesClaimListResponse,
)
def list_sales_claims(
    request: Request,
    project_id: list[UUID] | None = Query(default=None),
) -> SalesClaimListResponse:
    return sales_claims_list_sales_claims(request=request, project_id=project_id)


@router.get(
    "/api/sales-claims/overview",
    response_model=SalesClaimOverviewResponse,
)
def get_sales_claim_overview(request: Request) -> SalesClaimOverviewResponse:
    return sales_claims_get_sales_claim_overview(request)


@router.get("/api/sales-claims/export")
def download_sales_claims_workbook(
    request: Request,
    scope: str = Query(default="my"),
) -> StreamingResponse:
    return sales_claims_download_sales_claims_workbook(request=request, scope=scope)


@router.get(
    "/api/sales-claims/summary-by-user",
    response_model=SalesClaimSummaryByUserResponse,
)
def get_sales_claim_summary_by_user(request: Request) -> SalesClaimSummaryByUserResponse:
    return sales_claims_get_sales_claim_summary_by_user(request)
