from __future__ import annotations

import unittest

from backend.repositories.supabase_related_notice_publications import (
    SupabaseRelatedNoticePublicationRepository,
)


class SupabaseRelatedNoticePublicationRepositoryTests(unittest.TestCase):
    def test_missing_table_error_detects_schema_cache_message(self) -> None:
        message = "Could not find the table 'public.related_notice_publications' in the schema cache"
        self.assertTrue(SupabaseRelatedNoticePublicationRepository._is_missing_table_error(message))


if __name__ == "__main__":
    unittest.main()
