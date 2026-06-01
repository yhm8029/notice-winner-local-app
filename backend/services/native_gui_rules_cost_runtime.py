from __future__ import annotations

import re


COST_AMOUNT_UNIT_PATTERN = r"(?:\uC5B5\uC6D0|\uC5B5|\uCC9C\s*\uB9CC\s*\uC6D0|\uBC31\s*\uB9CC\s*\uC6D0|\uB9CC\s*\uC6D0|\uCC9C\s*\uC6D0|\uC6D0)"


def norm_space(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip().lower()


def extract_cost_won(value: str) -> int:
    txt = re.sub(r"\s+", "", str(value or ""))
    if not txt:
        return 0
    total = 0.0
    matched = False
    m_eok = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)\uC5B5\uC6D0", txt)
    if m_eok:
        total += float(m_eok.group(1).replace(",", "")) * 100000000
        matched = True
    if not m_eok:
        m_eok_bare = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)\uC5B5", txt)
        if m_eok_bare:
            total += float(m_eok_bare.group(1).replace(",", "")) * 100000000
            matched = True
    m_cheonman = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)\uCC9C\uB9CC\uC6D0", txt)
    if m_cheonman:
        total += float(m_cheonman.group(1).replace(",", "")) * 10000000
        matched = True
    m_baekman = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)\uBC31\uB9CC\uC6D0", txt)
    if m_baekman:
        total += float(m_baekman.group(1).replace(",", "")) * 1000000
        matched = True
    m_cheonwon = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)\uCC9C\uC6D0", txt)
    if m_cheonwon:
        total += float(m_cheonwon.group(1).replace(",", "")) * 1000
        matched = True
    m_man = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)\uB9CC\uC6D0", txt)
    if m_man:
        total += float(m_man.group(1).replace(",", "")) * 10000
        matched = True
    if not matched:
        m_won = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)\uC6D0", txt)
        if m_won:
            total += float(m_won.group(1).replace(",", ""))
            matched = True
    if not matched:
        digits = re.sub(r"[^0-9]", "", txt)
        if digits:
            try:
                total = float(digits)
                matched = True
            except Exception:
                matched = False
    return int(total) if matched else 0


def format_won(value: int | str) -> str:
    won = extract_cost_won(str(value or "")) if not isinstance(value, int) else int(value)
    if won <= 0:
        return ""
    return f"{won:,}\uC6D0"


def format_area_number(value: float) -> str:
    if int(value) == float(value):
        return f"{int(value):,}\u33A1"
    return f"{value:,.1f}\u33A1"


def extract_area_number(value: str) -> float:
    match = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)", str(value or ""))
    if not match:
        return 0.0
    try:
        return float(match.group(1).replace(",", ""))
    except Exception:
        return 0.0


def extract_labeled_cost_text(text: str, labels: tuple[str, ...]) -> str:
    source = str(text or "")
    if not source:
        return ""
    label_pattern = "|".join(re.escape(label) for label in labels)
    patterns = (
        re.compile(rf"(?:{label_pattern})\s*[:\uFF1A]?\s*((?:[0-9][0-9,]*(?:\.[0-9]+)?\s*{COST_AMOUNT_UNIT_PATTERN}))", re.I),
    )
    for pattern in patterns:
        match = pattern.search(source)
        if match:
            return format_won(match.group(1))
    return ""


def extract_notice_cost_won(text: str) -> int:
    source = str(text or "")
    if not source:
        return 0
    lines = [line.strip() for line in re.split(r"[\r\n]+", source) if line.strip()]
    construction_strong_tokens = (
        "\uC608\uC815\uACF5\uC0AC\uBE44",
        "\uC608\uC815 \uACF5\uC0AC\uBE44",
        "\uC608\uC0C1\uACF5\uC0AC\uBE44",
        "\uC608\uC0C1 \uACF5\uC0AC\uBE44",
        "\uCD94\uC815\uACF5\uC0AC\uBE44",
        "\uCD94\uC815 \uACF5\uC0AC\uBE44",
        "\uCD1D\uACF5\uC0AC\uBE44",
        "\uCD1D \uACF5\uC0AC\uBE44",
        "\uCD1D\uC608\uC815\uACF5\uC0AC\uBE44",
        "\uCD1D \uC608\uC815\uACF5\uC0AC\uBE44",
        "\uAC74\uCD95\uACF5\uC0AC\uBE44",
        "\uAC74\uCD95 \uACF5\uC0AC\uBE44",
    )
    budget_strong_tokens = ("\uCD1D\uC0AC\uC5C5\uBE44", "\uCD1D \uC0AC\uC5C5\uBE44", "\uC608\uC815\uC0AC\uC5C5\uBE44", "\uC608\uC815 \uC0AC\uC5C5\uBE44", "\uC608\uC0B0")
    construction_medium_tokens = ("\uACF5\uC0AC\uBE44",)
    budget_medium_tokens = ("\uC0AC\uC5C5\uBE44",)
    weak_tokens = (
        "\uC124\uACC4\uBE44",
        "\uC124\uACC4\uC6A9\uC5ED\uBE44",
        "\uC6A9\uC5ED\uBE44",
        "\uAD00\uB9AC\uC6A9\uC5ED",
        "\uAC10\uB9AC\uC6A9\uC5ED",
        "\uB3C4\uC11C\uC778\uC1C4\uBE44",
        "\uC6B4\uC601\uBE44",
    )
    hard_weak_tokens = ("\uB300\uB9AC\uBE44", "\uBCF4\uC0C1\uBE44", "\uBCF4\uD5D8\uB8CC", "\uC218\uC218\uB8CC")
    amount_patterns = (
        re.compile(rf"[0-9][0-9,]*(?:\.[0-9]+)?\s*{COST_AMOUNT_UNIT_PATTERN}"),
        re.compile(r"[0-9][0-9,]*(?:\.[0-9]+)?\s*\uC5B5\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*\uB9CC\uC6D0"),
    )

    def _extract_labeled_cost_candidates(labels: tuple[str, ...]) -> dict[int, int]:
        label_pattern = "|".join(re.escape(label) for label in labels)
        pattern = re.compile(
            rf"(?:{label_pattern})[\s\xa0:\uFF1A]{{0,8}}([\s\S]{{0,32}}?)"
            rf"([0-9][0-9,]*(?:\.[0-9]+)?\s*{COST_AMOUNT_UNIT_PATTERN})",
            re.I,
        )
        candidates: dict[int, int] = {}
        for match in pattern.finditer(source):
            won = extract_cost_won(match.group(2))
            if 100000000 <= won <= 5000000000000:
                candidates[won] = candidates.get(won, 0) + 1
        return candidates

    construction_labeled_candidates = _extract_labeled_cost_candidates(construction_strong_tokens)
    if construction_labeled_candidates:
        return max(
            construction_labeled_candidates.items(),
            key=lambda item: (item[1], item[0]),
        )[0]

    budget_labeled_candidates = _extract_labeled_cost_candidates(budget_strong_tokens)
    if budget_labeled_candidates:
        return max(
            budget_labeled_candidates.items(),
            key=lambda item: (item[1], item[0]),
        )[0]

    best_score_by_won: dict[int, int] = {}
    candidate_count_by_won: dict[int, int] = {}
    for index, line in enumerate(lines):
        prev_line = lines[index - 1] if index > 0 else ""
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        line_compact = norm_space(line)
        near_compact = norm_space(f"{prev_line} {line} {next_line}")
        for pattern in amount_patterns:
            for match in pattern.finditer(line):
                won = extract_cost_won(match.group(0))
                if not (100000000 <= won <= 5000000000000):
                    continue
                local = line[max(0, match.start() - 28) : min(len(line), match.end() + 28)]
                local_compact = norm_space(local)
                construction_strong_local = any(
                    token in local_compact for token in map(norm_space, construction_strong_tokens)
                )
                construction_strong_near = any(
                    token in near_compact for token in map(norm_space, construction_strong_tokens)
                )
                budget_strong_local = any(token in local_compact for token in map(norm_space, budget_strong_tokens))
                budget_strong_near = any(token in near_compact for token in map(norm_space, budget_strong_tokens))
                construction_medium_local = any(
                    token in local_compact for token in map(norm_space, construction_medium_tokens)
                )
                construction_medium_near = any(
                    token in near_compact for token in map(norm_space, construction_medium_tokens)
                )
                budget_medium_local = any(token in local_compact for token in map(norm_space, budget_medium_tokens))
                budget_medium_near = any(token in near_compact for token in map(norm_space, budget_medium_tokens))
                weak_local = any(token in local_compact for token in map(norm_space, weak_tokens))
                weak_near = any(token in near_compact for token in map(norm_space, weak_tokens))
                hard_weak_local = any(token in local_compact for token in map(norm_space, hard_weak_tokens))
                hard_weak_near = any(token in near_compact for token in map(norm_space, hard_weak_tokens))
                has_positive_cue = any(
                    (
                        construction_strong_local,
                        construction_strong_near,
                        budget_strong_local,
                        budget_strong_near,
                        construction_medium_local,
                        construction_medium_near,
                        budget_medium_local,
                        budget_medium_near,
                    )
                )
                has_local_positive_cue = any(
                    (
                        construction_strong_local,
                        budget_strong_local,
                        construction_medium_local,
                        budget_medium_local,
                    )
                )
                if (weak_local or weak_near) and not has_positive_cue:
                    continue
                score = 0
                if construction_strong_local:
                    score += 720
                elif not has_local_positive_cue and construction_strong_near:
                    score += 460
                if budget_strong_local:
                    score += 430
                elif not has_local_positive_cue and budget_strong_near:
                    score += 260
                if construction_medium_local:
                    score += 180
                elif not has_local_positive_cue and construction_medium_near:
                    score += 90
                if budget_medium_local:
                    score += 70
                elif not has_local_positive_cue and budget_medium_near:
                    score += 30
                if weak_local:
                    score -= 380
                elif not has_local_positive_cue and weak_near:
                    score -= 220
                if hard_weak_local:
                    score -= 240
                elif not has_local_positive_cue and hard_weak_near:
                    score -= 140
                if score < -80:
                    continue
                candidate_count_by_won[won] = candidate_count_by_won.get(won, 0) + 1
                prev_best = best_score_by_won.get(won, -(10**9))
                if score > prev_best:
                    best_score_by_won[won] = score
    if not best_score_by_won:
        return 0
    return max(
        best_score_by_won.items(),
        key=lambda item: (item[1], candidate_count_by_won.get(item[0], 0), item[0]),
    )[0]
