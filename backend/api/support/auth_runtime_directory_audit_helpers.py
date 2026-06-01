from __future__ import annotations

import time
from typing import Any


def touch_last_login(
    *,
    auth_user_id: str,
    request_json_fn,
    rest_base_url_fn,
    service_api_key_fn,
    timeout_seconds_fn,
    error_cls,
) -> None:
    if not auth_user_id:
        return
    try:
        request_json_fn(
            rest_url=rest_base_url_fn(),
            api_key=service_api_key_fn(),
            timeout_seconds=timeout_seconds_fn(),
            method="PATCH",
            path="/user_profiles",
            query=[("id", f"eq.{auth_user_id}")],
            headers={"Prefer": "return=minimal"},
            payload={"last_login_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
            error_cls=error_cls,
        )
    except error_cls:
        return


def append_audit_log(
    *,
    organization_id: str,
    actor_user_id: str = "",
    actor_membership_id: str = "",
    event_type: str,
    target_type: str = "",
    target_id: str = "",
    payload: dict[str, Any] | None = None,
    request_json_fn,
    rest_base_url_fn,
    service_api_key_fn,
    timeout_seconds_fn,
    error_cls,
) -> None:
    request_json_fn(
        rest_url=rest_base_url_fn(),
        api_key=service_api_key_fn(),
        timeout_seconds=timeout_seconds_fn(),
        method="POST",
        path="/audit_logs",
        headers={"Prefer": "return=minimal"},
        payload={
            "organization_id": organization_id or None,
            "actor_user_id": actor_user_id or None,
            "actor_membership_id": actor_membership_id or None,
            "event_type": event_type,
            "target_type": target_type,
            "target_id": target_id,
            "payload_json": payload or {},
        },
        allow_retry=False,
        error_cls=error_cls,
    )
