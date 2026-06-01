from __future__ import annotations

from collections import Counter
from typing import Any


def summarize_tracker_contact_sources(
    rows: list[dict[str, Any]],
    *,
    sample_limit: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    counts: Counter[str] = Counter()
    samples_by_source: dict[str, list[dict[str, str]]] = {}
    seen_values: dict[str, set[str]] = {}

    for row in rows:
        source = str(row.get("demand_contact_source") or "").strip() or "missing"
        contact = str(row.get("demand_contact") or "").strip()
        project_name = str(row.get("project_name") or row.get("contract_name") or "").strip()
        counts[source] += 1
        seen_for_source = seen_values.setdefault(source, set())
        if not contact or contact in seen_for_source:
            continue
        bucket = samples_by_source.setdefault(source, [])
        if len(bucket) >= sample_limit:
            continue
        bucket.append(
            {
                "project_name": project_name,
                "demand_contact": contact,
            }
        )
        seen_for_source.add(contact)

    source_counts = [
        {"source": source, "count": count}
        for source, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    source_samples = [
        {"source": source, "samples": samples_by_source.get(source, [])}
        for source, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    return {
        "source_counts": source_counts,
        "source_samples": source_samples,
    }
