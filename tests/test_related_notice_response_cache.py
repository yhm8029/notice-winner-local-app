from __future__ import annotations

import unittest
from uuid import uuid4

from backend.api.schemas import RelatedNoticeListResponse
from backend.services.related_notice_response_cache import related_notice_response_cache_ttl_seconds


class RelatedNoticeResponseCacheTests(unittest.TestCase):
    def test_pending_precompute_response_uses_longer_cache_ttl(self) -> None:
        response = RelatedNoticeListResponse(
            project_id=uuid4(),
            project_name="demo",
            project_search_name="demo",
            status="pending",
            source="precompute",
            message="precomputing",
            precomputed=False,
            items=[],
        )

        self.assertEqual(related_notice_response_cache_ttl_seconds(response), 30.0)


if __name__ == "__main__":
    unittest.main()
