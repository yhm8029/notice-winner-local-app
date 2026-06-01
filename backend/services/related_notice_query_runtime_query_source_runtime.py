from __future__ import annotations

import re


PROJECT_QUERY_SLUG_RE = re.compile(r"^[0-9A-Za-z가-힣]+(?:[-_][0-9A-Za-z가-힣]+){2,}$")


def coerce_project_query_source(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    if " " not in value and PROJECT_QUERY_SLUG_RE.fullmatch(value):
        value = re.sub(r"[-_]+", " ", value)
    return value
