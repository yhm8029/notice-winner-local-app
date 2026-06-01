from __future__ import annotations

from . import _native_export_backend_runtime_support as _runtime_support
from . import native_export_backend_runtime as _runtime

_EXPORT_NAMES = [name for name in dir(_runtime) if not name.startswith("__")]
globals().update({name: getattr(_runtime, name) for name in _EXPORT_NAMES})
__all__ = _EXPORT_NAMES

_RUNTIME_RUN_POST_COLLECT_NATIVE = _runtime.run_post_collect_native
_RUNTIME_BUILD_POST_COLLECT_OUTPUT_ROW = _runtime._build_post_collect_output_row
_RUNTIME_FETCH_ATTACHMENT_TEXTS = _runtime._fetch_attachment_texts
_RUNTIME_LOAD_ATTACHMENT_TEXT_WITH_TIMING = _runtime._load_attachment_text_with_timing
_RUNTIME_MAYBE_RESCUE_ATTACHMENT_FIELDS_WITH_SYNAP = _runtime._maybe_rescue_attachment_fields_with_synap


def _sync_runtime_globals(*names: str) -> None:
    for name in names:
        value = globals()[name]
        setattr(_runtime, name, value)
        setattr(_runtime_support, name, value)


def run_post_collect_native(
    internal_nav_csv: Path,
    out_csv: Path,
    *,
    params: dict[str, object] | None = None,
    progress_cb: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> Path:
    _sync_runtime_globals('_build_post_collect_output_row', 'load_llm_correction_config_from_options')
    return _RUNTIME_RUN_POST_COLLECT_NATIVE(
        internal_nav_csv,
        out_csv,
        params=params,
        progress_cb=progress_cb,
        should_stop=should_stop,
    )


def _build_post_collect_output_row(
    *,
    group_item: tuple[tuple[str, str], list[dict[str, str]]],
    llm_config: object,
    use_llm: bool,
    should_stop: Callable[[], bool] | None = None,
) -> tuple[dict[str, str], str, bool]:
    _sync_runtime_globals(
        'get_manual_field_overrides',
        'resolve_contract_by_bid_no',
        'get_last_contract_lookup_meta',
        'requests',
        '_fetch_page_documents',
        '_pick_primary_document',
        '_collect_attachment_documents',
        '_extract_notice_fields',
        '_load_attachment_text_with_timing',
        '_maybe_rescue_attachment_fields_with_synap',
        'maybe_correct_notice_fields_with_llm',
        'LlmCorrectionResult',
    )
    return _RUNTIME_BUILD_POST_COLLECT_OUTPUT_ROW(
        group_item=group_item,
        llm_config=llm_config,
        use_llm=use_llm,
        should_stop=should_stop,
    )


def _fetch_attachment_texts(documents: list[AttachmentDocument]) -> AttachmentTextPayload:
    _sync_runtime_globals('_load_attachment_text_with_timing')
    return _RUNTIME_FETCH_ATTACHMENT_TEXTS(documents)


def _load_attachment_text_with_timing(*, url: str, file_name: str) -> AttachmentTextLoadResult:
    _sync_runtime_globals('download_attachment_text', 'requests')
    return _RUNTIME_LOAD_ATTACHMENT_TEXT_WITH_TIMING(url=url, file_name=file_name)


def _maybe_rescue_attachment_fields_with_synap(
    *,
    extracted: ExtractedNoticeFields,
    attachment_url: str,
    file_name: str,
    bid_no: str,
    bid_ord: str,
    project_name: str,
    org_name: str,
    unty_atch_file_no: str,
) -> tuple[ExtractedNoticeFields, tuple[str, ...]]:
    _sync_runtime_globals('download_notice_attachment_text_via_synap', '_extract_notice_fields')
    return _RUNTIME_MAYBE_RESCUE_ATTACHMENT_FIELDS_WITH_SYNAP(
        extracted=extracted,
        attachment_url=attachment_url,
        file_name=file_name,
        bid_no=bid_no,
        bid_ord=bid_ord,
        project_name=project_name,
        org_name=org_name,
        unty_atch_file_no=unty_atch_file_no,
    )
