from __future__ import annotations

import os
import unittest
from datetime import datetime
from datetime import timezone
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

from backend.repositories.in_memory_related_notice_cache import InMemoryRelatedNoticeCacheRepository
from backend.repositories.factory import get_related_notice_publication_repository
from backend.repositories.factory import reset_related_notice_publication_repository
from backend.repositories.supabase_related_notice_publications import SupabaseRelatedNoticePublicationRepository
from backend.repositories.supabase_related_notice_publications import SupabaseRelatedNoticePublicationRepositoryConfig
from backend.repositories.factory import describe_repository_backends


class RepositoryFactoryTests(unittest.TestCase):
    def _assert_publication_row_contract(self, row: dict[str, object], *, organization_id: UUID, source_run_id: UUID) -> None:
        self.assertEqual(
            set(row.keys()),
            {
                "organization_id",
                "published_snapshot_set_id",
                "source_run_id",
                "generated_at",
                "published_at",
                "created_at",
                "updated_at",
            },
        )
        self.assertEqual(row["organization_id"], organization_id)
        self.assertEqual(row["source_run_id"], source_run_id)
        self.assertIsInstance(row["published_snapshot_set_id"], str)
        self.assertIsInstance(row["generated_at"], datetime)
        self.assertIsInstance(row["published_at"], datetime)
        self.assertIsInstance(row["created_at"], datetime)
        self.assertIsInstance(row["updated_at"], datetime)

    def test_defaults_to_in_memory_without_supabase_env(self) -> None:
        env = {
            "TRACKER_REPOSITORY_BACKEND": "",
            "RUN_REPOSITORY_BACKEND": "",
            "ARTIFACT_REPOSITORY_BACKEND": "",
            "RUN_LOG_REPOSITORY_BACKEND": "",
            "SUPABASE_URL": "",
            "SUPABASE_SECRET_KEY": "",
            "SUPABASE_SECRET": "",
            "SUPABASE_SERVICE_ROLE_KEY": "",
            "SUPABASE_ANON_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            summary = describe_repository_backends()

        self.assertEqual(summary["tracker_entries"], "in_memory")
        self.assertEqual(summary["runs"], "in_memory")
        self.assertEqual(summary["artifacts"], "in_memory")
        self.assertEqual(summary["logs"], "in_memory")
        self.assertEqual(summary["related_notice_cache"], "in_memory")
        self.assertEqual(summary.get("related_notice_publications"), "in_memory")
        self.assertEqual(summary["artifact_metadata_persistent"], False)

    def test_defaults_to_supabase_when_supabase_env_exists(self) -> None:
        env = {
            "TRACKER_REPOSITORY_BACKEND": "",
            "RUN_REPOSITORY_BACKEND": "",
            "ARTIFACT_REPOSITORY_BACKEND": "",
            "RUN_LOG_REPOSITORY_BACKEND": "",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SECRET_KEY": "sb_secret_example",
        }
        with patch.dict(os.environ, env, clear=False):
            summary = describe_repository_backends()

        self.assertEqual(summary["tracker_entries"], "supabase")
        self.assertEqual(summary["runs"], "supabase")
        self.assertEqual(summary["artifacts"], "supabase")
        self.assertEqual(summary["logs"], "supabase")
        self.assertEqual(summary["related_notice_cache"], "supabase")
        self.assertEqual(summary.get("related_notice_publications"), "supabase")
        self.assertEqual(summary["artifact_metadata_persistent"], True)

    def test_explicit_in_memory_overrides_supabase_default(self) -> None:
        env = {
            "TRACKER_REPOSITORY_BACKEND": "in_memory",
            "RUN_REPOSITORY_BACKEND": "",
            "ARTIFACT_REPOSITORY_BACKEND": "",
            "RUN_LOG_REPOSITORY_BACKEND": "",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SECRET_KEY": "sb_secret_example",
        }
        with patch.dict(os.environ, env, clear=False):
            summary = describe_repository_backends()

        self.assertEqual(summary["tracker_entries"], "in_memory")
        self.assertEqual(summary["runs"], "in_memory")
        self.assertEqual(summary["artifacts"], "in_memory")
        self.assertEqual(summary["logs"], "in_memory")
        self.assertEqual(summary["related_notice_cache"], "in_memory")
        self.assertEqual(summary.get("related_notice_publications"), "in_memory")
        self.assertEqual(summary["artifact_metadata_persistent"], False)

    def test_in_memory_related_notice_cache_reads_are_scoped_by_snapshot_set(self) -> None:
        repository = InMemoryRelatedNoticeCacheRepository()
        snapshot_set_a = "11111111-1111-1111-1111-111111111111"
        snapshot_set_b = "22222222-2222-2222-2222-222222222222"
        legacy_row = repository.upsert_cache(
            {
                "project_key": "project-alpha",
                "snapshot_set_id": "legacy",
                "payload_json": {"items": [{"id": "legacy"}]},
            }
        )

        repository.upsert_cache(
            {
                "project_key": "project-alpha",
                "snapshot_set_id": snapshot_set_a,
                "payload_json": {"items": [{"id": "a"}]},
            }
        )
        repository.upsert_cache(
            {
                "project_key": "project-alpha",
                "snapshot_set_id": snapshot_set_b,
                "payload_json": {"items": [{"id": "b"}]},
            }
        )

        try:
            row_a = repository.get_cache(project_key="project-alpha", snapshot_set_id=snapshot_set_a)
            row_b = repository.get_cache(project_key="project-alpha", snapshot_set_id=snapshot_set_b)
            row_default = repository.get_cache(project_key="project-alpha")
        except TypeError as exc:  # pragma: no cover - exercised by the failing red test
            self.fail(f"get_cache should accept snapshot_set_id: {exc}")

        self.assertEqual(row_a["snapshot_set_id"], snapshot_set_a)
        self.assertEqual(row_a["payload_json"], {"items": [{"id": "a"}]})
        self.assertEqual(row_b["snapshot_set_id"], snapshot_set_b)
        self.assertEqual(row_b["payload_json"], {"items": [{"id": "b"}]})
        self.assertEqual(row_default["snapshot_set_id"], "legacy")
        self.assertEqual(row_default["payload_json"], {"items": [{"id": "legacy"}]})
        self.assertEqual(legacy_row["snapshot_set_id"], "legacy")

    def test_in_memory_related_notice_cache_defaults_snapshot_set_to_legacy(self) -> None:
        repository = InMemoryRelatedNoticeCacheRepository()

        row = repository.upsert_cache(
            {
                "project_key": "project-beta",
                "payload_json": {"items": []},
            }
        )

        self.assertEqual(row["snapshot_set_id"], "legacy")
        self.assertEqual(repository.get_cache(project_key="project-beta", snapshot_set_id="legacy")["snapshot_set_id"], "legacy")

    def test_factory_related_notice_publication_repository_uses_explicit_publication_contract(self) -> None:
        organization_id = UUID("33333333-3333-3333-3333-333333333333")
        source_run_id = uuid4()
        generated_at = datetime(2026, 4, 8, 9, 30, tzinfo=timezone.utc)
        published_at = datetime(2026, 4, 8, 9, 31, tzinfo=timezone.utc)

        env = {
            "RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND": "in_memory",
            "RUN_REPOSITORY_BACKEND": "",
            "TRACKER_REPOSITORY_BACKEND": "",
        }
        with patch.dict(os.environ, env, clear=False):
            reset_related_notice_publication_repository()
            repository = get_related_notice_publication_repository()
            row = repository.upsert_publication(
                organization_id=organization_id,
                published_snapshot_set_id="snapshot-set-001",
                source_run_id=source_run_id,
                generated_at=generated_at,
                published_at=published_at,
            )
            loaded = repository.get_publication(organization_id=organization_id)

        self._assert_publication_row_contract(row, organization_id=organization_id, source_run_id=source_run_id)
        self._assert_publication_row_contract(loaded, organization_id=organization_id, source_run_id=source_run_id)
        self.assertEqual(loaded["published_snapshot_set_id"], "snapshot-set-001")

    def test_supabase_related_notice_publication_repository_normalizes_returned_row_shape(self) -> None:
        organization_id = UUID("33333333-3333-3333-3333-333333333333")
        source_run_id = uuid4()
        generated_at = datetime(2026, 4, 8, 9, 30, tzinfo=timezone.utc)
        published_at = datetime(2026, 4, 8, 9, 31, tzinfo=timezone.utc)

        config = SupabaseRelatedNoticePublicationRepositoryConfig(
            base_url="https://example.supabase.co",
            api_key="sb_secret_example",
            organization_id=str(organization_id),
        )
        response_row = {
            "organization_id": str(organization_id),
            "published_snapshot_set_id": "snapshot-set-001",
            "source_run_id": str(source_run_id),
            "generated_at": generated_at.isoformat(),
            "published_at": published_at.isoformat(),
            "created_at": generated_at.isoformat(),
            "updated_at": published_at.isoformat(),
        }
        with patch("backend.repositories.supabase_related_notice_publications.request_json") as request_json_mock:
            request_json_mock.side_effect = [([response_row], {}), ([response_row], {})]
            repository = SupabaseRelatedNoticePublicationRepository(config)
            row = repository.upsert_publication(
                organization_id=organization_id,
                published_snapshot_set_id="snapshot-set-001",
                source_run_id=source_run_id,
                generated_at=generated_at,
                published_at=published_at,
            )
            loaded = repository.get_publication(organization_id=organization_id)

        self._assert_publication_row_contract(row, organization_id=organization_id, source_run_id=source_run_id)
        self._assert_publication_row_contract(loaded, organization_id=organization_id, source_run_id=source_run_id)
        self.assertEqual(row["published_snapshot_set_id"], loaded["published_snapshot_set_id"])
