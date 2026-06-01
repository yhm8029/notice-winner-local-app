from __future__ import annotations

import json
from typing import Any


def to_auth_org_user_model(item: dict[str, Any], *, auth_org_user_item_cls: Any) -> Any:
    return auth_org_user_item_cls.model_validate(item)


def to_auth_invitation_model(*, invite_url_base: str, item: dict[str, Any], auth_invitation_item_cls: Any) -> Any:
    payload = dict(item)
    base_url = str(invite_url_base or "").rstrip("/")
    invite_token = str(payload.get("invite_token") or "")
    payload["invite_url"] = f"{base_url}/app/?invite_token={invite_token}" if invite_token else ""
    return auth_invitation_item_cls.model_validate(payload)


def to_auth_org_plan_summary_model(item: dict[str, Any], *, auth_org_plan_summary_cls: Any) -> Any:
    return auth_org_plan_summary_cls.model_validate(item)


def to_auth_audit_log_model(item: dict[str, Any], *, auth_audit_log_item_cls: Any) -> Any:
    return auth_audit_log_item_cls.model_validate(item)


def to_sales_claim_summary_project_model(item: dict[str, Any], *, sales_claim_summary_project_item_cls: Any) -> Any:
    return sales_claim_summary_project_item_cls.model_validate(item)


def to_sales_claim_summary_user_model(
    item: dict[str, Any],
    *,
    sales_claim_summary_user_item_cls: Any,
    to_sales_claim_summary_project_model: Any,
) -> Any:
    payload = dict(item or {})
    payload["projects"] = [
        to_sales_claim_summary_project_model(project)
        for project in list(payload.get("projects") or [])
    ]
    return sales_claim_summary_user_item_cls.model_validate(payload)


def model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def model_to_json_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    if hasattr(model, "json"):
        return json.loads(model.json())
    return model_to_dict(model)
