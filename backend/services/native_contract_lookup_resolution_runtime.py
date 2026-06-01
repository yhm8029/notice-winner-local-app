from __future__ import annotations

from collections.abc import Callable

from .native_contract_lookup_core_runtime_state import ContractLookupMeta
from .native_contract_lookup_core_runtime_state import ContractLookupResult
from .native_contract_lookup_core_runtime_state import _merge_contract_lookup_meta
from .native_contract_lookup_core_runtime_state import _set_last_contract_lookup_meta
from .native_contract_lookup_core_runtime_state import get_last_contract_lookup_meta


def _set_merged_lookup_meta(
    *,
    base_meta: ContractLookupMeta,
    contract_lookup_path: str,
    extra_meta: ContractLookupMeta | None = None,
) -> None:
    _set_last_contract_lookup_meta(
        _merge_contract_lookup_meta(
            base_meta,
            extra=extra_meta,
            contract_lookup_path=contract_lookup_path,
        )
    )


def resolve_ordered_contract_lookup_fallbacks(
    *,
    project_name_norm: str,
    announce_date: str,
    timeout_sec: float,
    org_name: str,
    resolve_eais_contract_hit_fn: Callable[..., ContractLookupResult | None],
    resolve_hub_result_hit_fn: Callable[..., ContractLookupResult | None],
    resolve_lofin_contract_hit_fn: Callable[..., ContractLookupResult | None],
    is_education_org_name_fn: Callable[[str], bool],
) -> ContractLookupResult | None:
    previous = get_last_contract_lookup_meta()
    eais_hit = resolve_eais_contract_hit_fn(
        project_name_norm=project_name_norm,
        announce_date=announce_date,
        timeout_sec=timeout_sec,
    )
    if eais_hit is not None:
        _set_merged_lookup_meta(base_meta=previous, contract_lookup_path="eais_hit")
        return eais_hit

    previous = get_last_contract_lookup_meta()
    hub_hit = resolve_hub_result_hit_fn(
        project_name_norm=project_name_norm,
        timeout_sec=timeout_sec,
    )
    if hub_hit is not None:
        _set_merged_lookup_meta(base_meta=previous, contract_lookup_path="hub_hit")
        return hub_hit

    if is_education_org_name_fn(org_name):
        _set_merged_lookup_meta(base_meta=previous, contract_lookup_path="no_hit")
        return None

    previous = get_last_contract_lookup_meta()
    lofin_hit = resolve_lofin_contract_hit_fn(
        project_name_norm=project_name_norm,
        announce_date=announce_date,
        timeout_sec=timeout_sec,
    )
    lofin_meta = get_last_contract_lookup_meta()
    _set_merged_lookup_meta(
        base_meta=previous,
        contract_lookup_path="lofin_hit" if lofin_hit is not None else "no_hit",
        extra_meta=lofin_meta,
    )
    return lofin_hit
