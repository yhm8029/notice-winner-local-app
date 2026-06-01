from __future__ import annotations

import re


REGION_NAME_SUFFIXES = ("특별시", "광역시", "특별자치시", "특별자치도", "도")
TRACKER_REGION_PREFIX_GUARDS = {"시", "군", "구", "읍", "면", "동"}


def split_region_city_from_address(
    value: str,
    *,
    official_region_pattern: str,
    match_official_sigungu,
) -> tuple[str, str]:
    text = str(value or "").strip()
    if not text:
        return "", ""
    region_match = re.search(rf"({official_region_pattern})", text)
    region = str(region_match.group(1) or "").strip() if region_match else ""
    city = match_official_sigungu(text, region=region)
    return region, city


def normalize_tracker_region_value(
    value: str,
    *,
    official_region_pattern: str,
    tracker_region_aliases,
    tracker_region_token_only_canonicals,
) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if re.fullmatch(rf"(?:{official_region_pattern})", raw):
        return raw
    return infer_tracker_region_from_text(
        raw,
        official_region_pattern=official_region_pattern,
        tracker_region_aliases=tracker_region_aliases,
        tracker_region_token_only_canonicals=tracker_region_token_only_canonicals,
    )


def infer_tracker_region_from_text(
    *values: str,
    official_region_pattern: str,
    tracker_region_aliases,
    tracker_region_token_only_canonicals,
) -> str:
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        match = re.search(rf"({official_region_pattern})", text)
        if match:
            return str(match.group(1) or "").strip()
        for canonical, aliases in tracker_region_aliases.items():
            for alias in sorted(aliases, key=len, reverse=True):
                if alias == canonical and canonical in tracker_region_token_only_canonicals:
                    matched = bool(re.search(rf"(?<![0-9A-Za-z가-힣]){re.escape(alias)}(?![0-9A-Za-z가-힣])", text))
                else:
                    matched = alias in text
                if matched:
                    return tracker_region_official_name(canonical, tracker_region_aliases=tracker_region_aliases)
    return ""


def tracker_region_official_name(canonical: str, *, tracker_region_aliases) -> str:
    aliases = tracker_region_aliases.get(str(canonical or "").strip(), ())
    if not aliases:
        return str(canonical or "").strip()
    for alias in reversed(aliases):
        if alias.endswith(REGION_NAME_SUFFIXES):
            return alias
    return aliases[-1]


def strip_region_prefix_from_candidate(value: str, region: str, *, tracker_region_aliases) -> str:
    text = str(value or "").strip()
    canonical = ""
    for key, aliases in tracker_region_aliases.items():
        if region == key or region in aliases:
            canonical = key
            break
    if not canonical:
        return text
    aliases = sorted(tracker_region_aliases.get(canonical, ()), key=len, reverse=True)
    stripped = text
    changed = True
    while changed:
        changed = False
        for alias in aliases:
            if stripped.startswith(alias):
                candidate = stripped[len(alias) :].strip()
                if candidate in TRACKER_REGION_PREFIX_GUARDS:
                    continue
                stripped = candidate
                changed = True
                break
    return stripped


def normalize_tracker_site_city_candidate(
    candidate: str,
    *,
    region: str,
    tracker_region_aliases,
    tracker_site_city_noise_exact,
    tracker_site_city_noise_parts,
    invalid_city_location_tokens,
    match_official_sigungu,
) -> str:
    value = str(candidate or "").strip()
    if not value:
        return ""
    value = strip_region_prefix_from_candidate(
        value,
        region,
        tracker_region_aliases=tracker_region_aliases,
    ).strip()
    if not value:
        return ""
    if value in tracker_site_city_noise_exact:
        return ""
    if any(token in value for token in tracker_site_city_noise_parts):
        return ""
    if value == region:
        return ""
    if value == "119구" or re.fullmatch(r"\d+구", value):
        return ""
    if any(token in value for token in invalid_city_location_tokens):
        return ""
    if value.endswith(REGION_NAME_SUFFIXES):
        return ""
    official = match_official_sigungu(value, region=region)
    if official:
        return official
    return ""


def tracker_site_city_rank(value: str) -> int:
    text = str(value or "").strip()
    if text.endswith("구"):
        return 3
    if text.endswith(("시", "군")):
        return 2
    if text.endswith(("읍", "면")):
        return 1
    if text.endswith("동"):
        return 0
    return -1
