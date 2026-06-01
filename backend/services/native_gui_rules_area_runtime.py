from __future__ import annotations

import re

from .native_gui_rules_cost_runtime import extract_area_number
from .native_gui_rules_cost_runtime import format_area_number


def is_building_like_project(project_name: str) -> bool:
    pname = str(project_name or "")
    return any(
        token in pname
        for token in (
            "설계공모",
            "설계용역",
            "기본 및 실시설계",
            "기본·실시설계",
            "건립",
            "신축",
            "증축",
            "개축",
            "리모델링",
            "복합센터",
            "도서관",
            "학교",
            "센터",
            "청사",
            "회관",
            "생활문화",
            "문화센터",
        )
    )


def extract_notice_area_value(text: str, project_name: str = "") -> str:
    source = str(text or "")
    if not source:
        return ""
    lines = [line.strip() for line in re.split(r"[\r\n]+", source) if line.strip()]
    flat = re.sub(r"\s+", " ", source).strip()
    strong_label_pat = re.compile(
        r"(?:\ucd1d\s*\uc5f0\uba74\uc801|\uac74\ucd95\s*\uc5f0\uba74\uc801|\uad50\uc0ac\s*\uba74\uc801|\uc5f0\uba74\uc801|\uc804\uccb4\s*\uc5f0\uba74\uc801|\uc0ac\uc5c5\s*\uba74\uc801|\uc870\uc131\s*\uba74\uc801|\ub300\uc0c1\s*\uba74\uc801)",
        re.I,
    )
    medium_label_pat = re.compile(r"(?:\uc0ac\uc5c5\s*\uaddc\ubaa8|\uac74\ucd95\s*\uaddc\ubaa8|\uaddc\ubaa8)", re.I)
    weak_label_pat = re.compile(r"(?:\uac74\ucd95\s*\uba74\uc801|\uc2dc\uc124\s*\uaddc\ubaa8)", re.I)
    bad_label_pat = re.compile(r"(?:\ub300\uc9c0\s*\uba74\uc801|\ubd80\uc9c0\s*\uba74\uc801|\ub300\uc9c0\s*\uc704\uce58|\ubd80\uc9c0\s*\uc704\uce58)", re.I)
    soft_bad_pat = re.compile(r"(?:\ub300\uc9c0|\ubd80\uc9c0)", re.I)
    unit_pat = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:\u33a1|m2|m\u00b2|\uc81c\uacf1\ubbf8\ud130)", re.I)
    plain_num_pat = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)")
    explicit_medium_label_pat = re.compile(r"(?:\uc0ac\uc5c5\s*\uaddc\ubaa8|\uac74\ucd95\s*\uaddc\ubaa8|\uc2dc\uc124\s*\uaddc\ubaa8)", re.I)
    list_marker_pat = re.compile(r"^\s*(?:\d{1,2}[)\.]|[\u2460-\u2473]|[가-힣A-Za-z]\))")
    cost_label_pat = re.compile(
        r"(?:\ucd1d\s*\uacf5\uc0ac\ube44|\uc608\uc815\s*\ucd1d\s*\uacf5\uc0ac\ube44|\ucd94\uc815\s*\uacf5\uc0ac\ube44|\uacf5\uc0ac\ube44|\ucd1d\s*\uc0ac\uc5c5\ube44|\uc0ac\uc5c5\ube44|\uc124\uacc4\ube44|\uc6a9\uc5ed\ube44|\uc608\uc0b0)",
        re.I,
    )
    part_sum_pat = re.compile(
        r"(\ubcf5\uc6d0\uba74\uc801|\uc99d\ucd95\uba74\uc801|\uc2e0\ucd95\uba74\uc801|\uac1c\ucd95\uba74\uc801|\uc99d\uac1c\ucd95\uba74\uc801|\ub9ac\ubaa8\ub378\ub9c1\uba74\uc801|\uae30\uc874\uc5f0\uba74\uc801|\uc2e0\uc124\uc5f0\uba74\uc801)"
        r"[^0-9]{0,20}([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:\u33a1|m2|m\u00b2|\uc81c\uacf1\ubbf8\ud130)",
        re.I,
    )

    def _is_reference_area_context(window: str) -> bool:
        compact_window = re.sub(r"\s+", "", str(window or ""))
        if not compact_window:
            return False
        if re.search(r"(\uc2e4\uc801|\ucc38\uac00\uc790\uaca9|\uc785\ucc30\uc790\uaca9|\ub4f1\ub85d\uc77c|\uc218\ud589\uc2e4\uc801)", compact_window):
            return True
        if re.search(r"(\uc774\uc0c1|\ubbf8\ub9cc|\ucd08\uacfc)", compact_window) and re.search(
            r"(\uc790\uaca9|\uc218\ud589|\uacfc\uc5c5|\uc6a9\uc5ed)",
            compact_window,
        ):
            return True
        return False

    after_project_subtotal = _extract_after_project_subtotal_area(lines, unit_pat)
    if after_project_subtotal:
        return format_area_number(after_project_subtotal)

    floor_use_table_area = _extract_floor_use_table_area(lines, cost_label_pat, plain_num_pat)
    if floor_use_table_area:
        return format_area_number(floor_use_table_area)

    site_gross_table_pat = re.compile(
        r"(?:\ub300\uc9c0\s*\uba74\uc801|\ubd80\uc9c0\s*\uba74\uc801)"
        r"[\s\S]{0,80}?(?:\ucd94\uc815\s*\uc5f0\s*\uba74\s*\uc801|\uac74\ucd95\s*\uc5f0\s*\uba74\s*\uc801|\uc5f0\s*\uba74\s*\uc801)"
        r"[\s\S]{0,160}?"
        r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:\u33a1|m2|m\u00b2|\uc81c\uacf1\ubbf8\ud130)"
        r"[\s\S]{0,40}?"
        r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:\u33a1|m2|m\u00b2|\uc81c\uacf1\ubbf8\ud130)",
        re.I,
    )
    for match in site_gross_table_pat.finditer(source):
        try:
            site_value = float(match.group(1).replace(",", ""))
            gross_value = float(match.group(2).replace(",", ""))
        except Exception:
            continue
        if 50 <= gross_value <= 2000000 and site_value != gross_value:
            return format_area_number(gross_value)

    sf_metric_area_pat = re.compile(
        r"(?:\ucd1d\s*\uc5f0\s*\uba74\s*\uc801|\uac74\ucd95\s*\uc5f0\s*\uba74\s*\uc801|\uc5f0\s*\uba74\s*\uc801)"
        r"[^0-9]{0,40}[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:SF|sq\.?\s*ft\.?|square\s*feet)"
        r"\s*\(\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:\u33a1|m2|m\u00b2|\uc81c\uacf1\ubbf8\ud130)\s*\)",
        re.I,
    )
    for match in sf_metric_area_pat.finditer(flat):
        try:
            value = float(match.group(1).replace(",", ""))
        except Exception:
            continue
        if 50 <= value <= 2000000:
            return format_area_number(value)

    direct_area_pat = re.compile(
        r"(?:\ucd1d\s*\uc5f0\s*\uba74\s*\uc801|\uac74\ucd95\s*\uc5f0\s*\uba74\s*\uc801|\uad50\uc0ac\s*\uba74\uc801|\uac1c\ucd95\s*\uc5f0\s*\uba74\s*\uc801|\uc5f0\s*\uba74\s*\uc801|\uc804\uccb4\s*\uc5f0\s*\uba74\s*\uc801|\uc0ac\uc5c5\s*\uba74\uc801|\uc870\uc131\s*\uba74\uc801|\ub300\uc0c1\s*\uba74\uc801|area)\s*[:\uff1a]?\s*(?:approximately\s*)?"
        r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:\u33a1|m2|m\u00b2)?",
        re.I,
    )
    direct_area_multi_pat = re.compile(
        r"(?:\ucd1d\s*\uc5f0\s*\uba74\s*\uc801|\uac74\ucd95\s*\uc5f0\s*\uba74\s*\uc801|\uad50\uc0ac\s*\uba74\uc801|\uac1c\ucd95\s*\uc5f0\s*\uba74\s*\uc801|\uc5f0\s*\uba74\s*\uc801|\uc804\uccb4\s*\uc5f0\s*\uba74\s*\uc801)"
        r"[^0-9]{0,20}((?:[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:\u33a1|m2|m\u00b2)\s*){2,})",
        re.I,
    )
    for match in direct_area_multi_pat.finditer(flat):
        multi_values: list[float] = []
        for unit_match in unit_pat.finditer(match.group(1)):
            try:
                value = float(unit_match.group(1).replace(",", ""))
            except Exception:
                continue
            if 50 <= value <= 2000000:
                multi_values.append(value)
        if len(multi_values) >= 2:
            return format_area_number(sum(multi_values))

    for match in direct_area_pat.finditer(flat):
        left = flat[max(0, match.start() - 40) : match.start()]
        if re.search(r"(\ubd80\uc9c0|\ub300\uc9c0)", left):
            continue
        around = flat[match.start() : min(len(flat), match.end() + 8)]
        if "%" in around:
            continue
        reference_window = flat[max(0, match.start() - 90) : min(len(flat), match.end() + 90)]
        if _is_reference_area_context(reference_window):
            continue
        try:
            value = float(match.group(1).replace(",", ""))
        except Exception:
            continue
        if 50 <= value <= 2000000:
            return format_area_number(value)

    header_indices = [
        index
        for index, line in enumerate(lines)
        if "\uc5f0\uba74\uc801" in re.sub(r"\s+", "", line)
    ]
    for header_index in header_indices:
        subtotal_context = lines[header_index : min(len(lines), header_index + 16)]
        for candidate_line in subtotal_context:
            subtotal_match = re.search(
                r"^\s*(?:\uacc4|\ud569\uacc4)\s*[:\uff1a-]?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
                candidate_line,
                flags=re.I,
            )
            if not subtotal_match:
                continue
            try:
                subtotal_value = float(subtotal_match.group(1).replace(",", ""))
            except Exception:
                continue
            if 50 <= subtotal_value <= 2000000:
                return format_area_number(subtotal_value)

    pyeong_header_indices = [
        index
        for index, line in enumerate(lines)
        if "\uba74\uc801" in re.sub(r"\s+", "", line) and "\ud3c9" in line
    ]
    for header_index in pyeong_header_indices:
        subtotal_context = lines[header_index + 1 : min(len(lines), header_index + 12)]
        for candidate_line in subtotal_context:
            if cost_label_pat.search(candidate_line):
                continue
            subtotal_match = re.search(
                r"(?:^|\s)(?:\ud569\uacc4|\ucd1d\uacc4)\s*[:\uff1a-]?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\b",
                candidate_line,
                flags=re.I,
            )
            if not subtotal_match:
                continue
            try:
                subtotal_pyeong = float(subtotal_match.group(1).replace(",", ""))
            except Exception:
                continue
            subtotal_sqm = subtotal_pyeong * 3.305785
            if 50 <= subtotal_sqm <= 2000000:
                return format_area_number(subtotal_sqm)

    scored: list[tuple[int, float]] = []
    for index, line in enumerate(lines):
        compact = re.sub(r"\s+", "", line)
        has_strong = bool(strong_label_pat.search(compact))
        has_medium = bool(medium_label_pat.search(compact))
        has_weak = bool(weak_label_pat.search(compact))
        has_bad = bool(bad_label_pat.search(compact))
        if not (has_strong or has_medium or has_weak):
            continue
        if has_bad and not has_strong:
            continue
        context_end = index + (3 if has_medium and not has_strong else 2)
        context = " ".join(lines[max(0, index - 1) : min(len(lines), context_end)])
        context_compact = re.sub(r"\s+", "", context)
        context_has_strong = bool(strong_label_pat.search(context_compact))
        context_has_bad = bool(bad_label_pat.search(context_compact))
        context_has_soft_bad = bool(soft_bad_pat.search(context))
        if not has_strong and not has_medium and not context_has_strong:
            continue

        nums: list[float] = []
        for match in unit_pat.finditer(context):
            try:
                value = float(match.group(1).replace(",", ""))
            except Exception:
                continue
            if not (50 <= value <= 2000000):
                continue
            left = context[max(0, match.start() - 30) : match.start()]
            local_window = context[max(0, match.start() - 16) : min(len(context), match.end() + 16)]
            if re.search(r"(\uac01\s*\uce35|\uce35\ub2f9|1\uce35|2\uce35|\uc9c0\uc0c1\d+\uce35|\uc9c0\ud558\d+\uce35|\uce35\s*\ubc14\ub2e5)", left):
                continue
            if bad_label_pat.search(local_window):
                continue
            nums.append(value)

        strong_direct = re.search(
            r"(?:\ucd1d\s*\uc5f0\s*\uba74\s*\uc801|\uac74\ucd95\s*\uc5f0\s*\uba74\s*\uc801|\uad50\uc0ac\s*\uba74\uc801|\uac1c\ucd95\s*\uc5f0\s*\uba74\s*\uc801|\uc5f0\s*\uba74\s*\uc801|\uc804\uccb4\s*\uc5f0\s*\uba74\uc801)[^0-9]{0,80}([0-9][0-9,]*(?:\.[0-9]+)?)",
            context_compact,
            re.I,
        )
        medium_direct = re.search(
            r"(?:\uac74\ucd95\s*\uaddc\ubaa8|\uc0ac\uc5c5\s*\uaddc\ubaa8)[^0-9]{0,80}([0-9][0-9,]*(?:\.[0-9]+)?)",
            context_compact,
            re.I,
        )
        picked = strong_direct or (medium_direct if has_medium else None)
        if not nums and (has_strong or has_medium):
            if picked:
                try:
                    picked_value = float(picked.group(1).replace(",", ""))
                except Exception:
                    picked_value = 0.0
                picked_context = context_compact[max(0, picked.start() - 24) : min(len(context_compact), picked.end() + 24)]
                if cost_label_pat.search(picked_context):
                    picked_value = 0.0
                if 50 <= picked_value <= 2000000:
                    nums = [picked_value]
            elif len(lines) > index + 1:
                next_line = lines[index + 1]
                next_num = plain_num_pat.search(next_line)
                if next_num and not list_marker_pat.search(next_line):
                    try:
                        next_value = float(next_num.group(1).replace(",", ""))
                    except Exception:
                        next_value = 0.0
                    if next_value >= 50 and (has_strong or explicit_medium_label_pat.search(compact)):
                        nums = [next_value]

        if not nums:
            continue

        part_nums: list[float] = []
        for part_match in part_sum_pat.finditer(context_compact):
            try:
                part_value = float(part_match.group(2).replace(",", ""))
            except Exception:
                continue
            if 50 <= part_value <= 2000000:
                part_nums.append(part_value)

        fallback_area_value = sum(part_nums) if len(part_nums) >= 2 else max(nums)
        if picked:
            try:
                picked_value = float(picked.group(1).replace(",", ""))
            except Exception:
                picked_value = 0.0
            picked_window = context_compact[max(0, picked.start() - 12) : min(len(context_compact), picked.end() + 12)]
            if cost_label_pat.search(context_compact[max(0, picked.start() - 24) : min(len(context_compact), picked.end() + 24)]):
                picked_value = 0.0
            if picked_value < 50 and re.search(r"(%|\u00b1|\uc774\ub0b4|\uce35|\uc9c0\ud558|\uc9c0\uc0c1)", picked_window):
                picked_value = 0.0
            area_value = picked_value if 50 <= picked_value <= 2000000 else fallback_area_value
        else:
            area_value = fallback_area_value
        if area_value < 50:
            continue
        score = 0
        if has_strong:
            score += 360
        elif has_medium:
            score += 240
        elif has_weak:
            score += 140
        if len(part_nums) >= 2:
            score += 70
        if context_has_strong:
            score += 120
        if context_has_bad and not context_has_strong:
            score -= 260
        elif context_has_soft_bad and not context_has_strong:
            score -= 200
        if re.search(r"(\u00b1|\ubc94\uc704|\uc870\uc815\s*\uac00\ub2a5|\uc774\ub0b4)", context_compact):
            score += 15
        scored.append((score, area_value))

    if not scored:
        return ""
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if is_building_like_project(project_name):
        for _score, candidate_value in scored:
            area = format_area_number(candidate_value)
            area_n = extract_area_number(area)
            if area_n >= 100:
                return area
        first_area = format_area_number(scored[0][1])
        first_area_n = extract_area_number(first_area)
        if 0 < first_area_n < 100:
            return ""
        return first_area
    area = format_area_number(scored[0][1])
    return area


def _extract_after_project_subtotal_area(lines: list[str], unit_pat: re.Pattern[str]) -> float:
    for index, line in enumerate(lines):
        compact = re.sub(r"\s+", "", line)
        if "\uc5f0\uba74\uc801" not in compact:
            continue
        context_lines = lines[index : min(len(lines), index + 45)]
        context_compact = re.sub(r"\s+", "", " ".join(context_lines))
        if not re.search(r"(\uae30\uc874|\uc0ac\uc5c5\uc804)", context_compact):
            continue
        if not re.search(r"(\uc0ac\uc5c5\ud6c4|\uc99d\uac1c\ucd95|\uacc4\ud68d\ud6c4)", context_compact):
            continue
        for candidate_index, candidate_line in enumerate(context_lines):
            if not re.search(r"(\uc18c\uacc4|\ud569\uacc4|\uacc4)", re.sub(r"\s+", "", candidate_line)):
                continue
            values: list[float] = []
            candidate_context = " ".join(context_lines[candidate_index : min(len(context_lines), candidate_index + 8)])
            for match in unit_pat.finditer(candidate_context):
                try:
                    value = float(match.group(1).replace(",", ""))
                except Exception:
                    continue
                if 50 <= value <= 2000000:
                    values.append(value)
            if len(values) >= 3:
                return values[1]
    return 0.0


def _extract_floor_use_table_area(
    lines: list[str],
    cost_label_pat: re.Pattern[str],
    plain_num_pat: re.Pattern[str],
) -> float:
    for index, line in enumerate(lines):
        compact = re.sub(r"\s+", "", line)
        if "\uce35\ubcc4\uc6a9\ub3c4" not in compact:
            continue
        context = lines[index : min(len(lines), index + 12)]
        context_compact = re.sub(r"\s+", "", " ".join(context))
        if "\uba74\uc801" not in context_compact:
            continue
        for candidate_line in context:
            candidate_compact = re.sub(r"\s+", "", candidate_line)
            if not candidate_compact or cost_label_pat.search(candidate_line):
                continue
            if re.search(r"(\uad6c\ubd84|\uba74\uc801|\ucc38\uace0|\uacc4\ud68d|\uce35|~)", candidate_compact):
                continue
            match = plain_num_pat.search(candidate_line)
            if not match:
                continue
            try:
                value = float(match.group(1).replace(",", ""))
            except Exception:
                continue
            if 50 <= value <= 2000000:
                return value
    return 0.0
