from __future__ import annotations

from . import native_gui_rules_impl as _impl

_REEXPORTED_NAMES = (
    "CONTACT_DEPT_SENTENCE_NOISE_PAT",
    "CONTACT_OTHER_SENTENCE_FRAGMENT_PAT",
    "ContactObservation",
    "ContactResolution",
    "INVALID_CITY_LOCATION_TOKENS",
    "OFFICIAL_REGION_PATTERN",
    "PHONE_FLEX_PAT",
    "WinnerExtraction",
    "_looks_like_attachment_filename_line",
    "decode_html_and_strip",
    "extract_area_number",
    "extract_client_location",
    "extract_completion_expected_date",
    "extract_construction_start_date",
    "extract_contact_from_notice_text",
    "extract_contact_observations_from_notice_text",
    "extract_contact_resolution_from_notice_text",
    "extract_cost_won",
    "extract_duration_days_from_text",
    "extract_labeled_cost_text",
    "extract_notice_area_value",
    "extract_notice_cost_won",
    "extract_site_location",
    "format_area_number",
    "format_won",
    "get_manual_field_overrides",
    "has_external_competition_portal_only_contact",
    "infer_city_from_org_or_project",
    "infer_region_from_org",
    "is_auxiliary_service_project",
    "is_building_like_project",
    "looks_like_architecture_firm_name",
    "normalize_contact_candidate",
    "normalize_phone",
    "resolve_contact_from_observations",
    "winner_name_extractor",
)

for _name in _REEXPORTED_NAMES:
    globals()[_name] = getattr(_impl, _name)

__all__ = list(_REEXPORTED_NAMES)
