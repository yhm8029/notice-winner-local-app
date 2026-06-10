from __future__ import annotations

from scripts.build_notice_viewer_cache import entry_has_cached_synap_url
from scripts.build_notice_viewer_cache import select_uncached_entries


def test_entry_has_cached_synap_url_matches_bid_and_order_prefix() -> None:
    entry = {"id": "entry-1", "source_bid_no": " r26bk001 ", "source_bid_ord": "1"}
    cache = {
        "R26BK001|001|1|": "https://www.g2b.go.kr/SynapDocViewServer/viewer/doc.html?key=abc",
        "R26BK999|001|1|": "https://www.g2b.go.kr/SynapDocViewServer/viewer/doc.html?key=other",
    }

    assert entry_has_cached_synap_url(entry, cache) is True


def test_select_uncached_entries_skips_cached_entries_and_entries_without_ids() -> None:
    rows = [
        {"id": "cached", "source_bid_no": "R26BK001", "source_bid_ord": "000"},
        {"id": "missing-cache", "source_bid_no": "R26BK002", "source_bid_ord": "000"},
        {"source_bid_no": "R26BK003", "source_bid_ord": "000"},
    ]
    cache = {
        "R26BK001|000|1|": "https://www.g2b.go.kr/SynapDocViewServer/viewer/doc.html?key=abc",
    }

    assert select_uncached_entries(rows, cache) == [
        {"id": "missing-cache", "source_bid_no": "R26BK002", "source_bid_ord": "000"},
    ]
