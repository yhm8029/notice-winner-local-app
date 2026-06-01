from __future__ import annotations

from datetime import datetime
from datetime import timezone
from types import SimpleNamespace
from uuid import UUID

import unittest
from unittest.mock import Mock
from unittest.mock import patch

from backend.api.schemas import RelatedNoticeItem
from backend.api.schemas import RelatedNoticeListResponse
from backend.phase1_defaults import PROJECT_TRACKER_RUN_TYPE
from backend.phase1_defaults import build_phase1_run_row
from backend.repositories.in_memory_related_notice_cache import InMemoryRelatedNoticeCacheRepository
from backend.repositories.in_memory_related_notice_publications import InMemoryRelatedNoticePublicationRepository
from backend.repositories.in_memory_runs import InMemoryRunRepository
from backend.services import run_execution
from backend.services.related_notice_publish_backend import publish_related_notice_snapshot_set_for_run
from backend.services.related_notice_response_cache import clear_related_notice_response_cache
from backend.services.related_notice_response_cache import get_related_notice_response_cache
from backend.services.related_notice_response_cache import set_related_notice_response_cache


class _RecordingArtifactRepository:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def list_artifacts(self, *, run_id: UUID) -> list[dict[str, object]]:
        del run_id
        return [dict(row) for row in self.rows]

    def create_artifact(self, row: dict[str, object]) -> dict[str, object]:
        stored = dict(row)
        self.rows.append(stored)
        return stored


class _MutatingFailingPublicationRepository:
    def __init__(self, initial_row: dict[str, object]) -> None:
        self._row = dict(initial_row)
        self._upsert_calls = 0

    def get_publication(self, *, organization_id: UUID) -> dict[str, object] | None:
        if self._row.get("organization_id") != organization_id:
            return None
        return dict(self._row)

    def upsert_publication(
        self,
        *,
        organization_id: UUID,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: object,
        published_at: object,
    ) -> dict[str, object]:
        self._upsert_calls += 1
        row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": str(published_snapshot_set_id or ""),
            "source_run_id": source_run_id,
            "generated_at": generated_at,
            "published_at": published_at,
            "created_at": self._row.get("created_at") or generated_at,
            "updated_at": published_at,
        }
        if self._upsert_calls == 1:
            self._row = dict(row)
            raise RuntimeError("publish failed after live pointer mutation")
        self._row = dict(row)
        return dict(row)

    def upsert_publication_if_current(self, **kwargs: object) -> dict[str, object]:
        expected_updated_at = kwargs.pop("expected_updated_at", None)
        current_row = self.get_publication(organization_id=kwargs["organization_id"])  # type: ignore[index]
        if current_row is not None and current_row.get("updated_at") != expected_updated_at:
            return current_row
        return self.upsert_publication(**kwargs)


class _RacingPublicationRepository(InMemoryRelatedNoticePublicationRepository):
    def __init__(self, *, initial_row: dict[str, object], raced_row: dict[str, object]) -> None:
        super().__init__()
        organization_id = str(initial_row["organization_id"])
        self._rows_by_organization_id[organization_id] = dict(initial_row)
        self._raced_row = dict(raced_row)
        self._raced = False

    def get_publication(self, *, organization_id: UUID) -> dict[str, object] | None:
        row = super().get_publication(organization_id=organization_id)
        if row is not None and not self._raced:
            self._raced = True
            self._rows_by_organization_id[str(organization_id)] = dict(self._raced_row)
        return row


class _ConcurrentCandidatePublicationRepository(InMemoryRelatedNoticePublicationRepository):
    def __init__(
        self,
        *,
        initial_row: dict[str, object],
        candidate_row: dict[str, object],
        republished_row: dict[str, object],
    ) -> None:
        super().__init__()
        organization_id = str(initial_row["organization_id"])
        self._rows_by_organization_id[organization_id] = dict(initial_row)
        self._candidate_row = dict(candidate_row)
        self._republished_row = dict(republished_row)
        self._published_once = False
        self._republished = False

    def get_publication(self, *, organization_id: UUID) -> dict[str, object] | None:
        row = super().get_publication(organization_id=organization_id)
        if row is not None and self._published_once and not self._republished:
            self._republished = True
            self._rows_by_organization_id[str(organization_id)] = dict(self._republished_row)
            return dict(self._republished_row)
        return row

    def upsert_publication_if_current(
        self,
        *,
        organization_id: UUID,
        expected_updated_at: object,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: object,
        published_at: object,
    ) -> dict[str, object]:
        if not self._published_once:
            current_row = self.get_publication(organization_id=organization_id)
            if current_row is not None and current_row.get("updated_at") != expected_updated_at:
                return current_row
            self._published_once = True
            self._rows_by_organization_id[str(organization_id)] = dict(self._candidate_row)
            raise RuntimeError("publish failed after candidate cutover")
        return super().upsert_publication_if_current(
            organization_id=organization_id,
            expected_updated_at=expected_updated_at,
            published_snapshot_set_id=published_snapshot_set_id,
            source_run_id=source_run_id,
            generated_at=generated_at,
            published_at=published_at,
        )


class RelatedNoticePublishBackendTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_related_notice_response_cache()

    def test_publish_related_notice_snapshot_set_writes_candidate_rows_and_pointer(self) -> None:
        organization_id = UUID("44444444-4444-4444-4444-444444444444")
        run_id = UUID("55555555-5555-5555-5555-555555555555")
        generated_at = datetime(2026, 4, 8, 9, 30, tzinfo=timezone.utc)
        published_at = datetime(2026, 4, 8, 9, 31, tzinfo=timezone.utc)
        payload = {
            "run_id": str(run_id),
            "generated_at": generated_at.isoformat(),
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-1"}, {"id": "notice-2"}],
                }
            ],
        }
        cache_repository = InMemoryRelatedNoticeCacheRepository()
        publication_repository = InMemoryRelatedNoticePublicationRepository()

        with patch(
            "backend.services.related_notice_publish_backend.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_publication_repository",
            return_value=publication_repository,
        ):
            result = publish_related_notice_snapshot_set_for_run(
                run_id=run_id,
                related_notice_payload=payload,
                utc_now_fn=lambda: published_at,
            )

        snapshot_set_id = str(run_id)
        cached_row = cache_repository.get_cache(project_key="project-alpha", snapshot_set_id=snapshot_set_id)
        publication_row = publication_repository.get_publication(organization_id=organization_id)

        self.assertIsNotNone(cached_row)
        assert cached_row is not None
        self.assertEqual(cached_row["snapshot_set_id"], snapshot_set_id)
        self.assertEqual(cached_row["project_key"], "project-alpha")
        self.assertEqual(cached_row["project_name"], "Alpha Project")
        self.assertEqual(cached_row["project_search_name"], "alpha project")
        self.assertEqual(cached_row["issuer_name"], "City of Seoul")
        self.assertEqual(cached_row["status"], "success")
        self.assertEqual(cached_row["source"], "precomputed")
        self.assertEqual(cached_row["algorithm_version"], 11)
        self.assertEqual(cached_row["item_count"], 2)
        self.assertEqual(cached_row["source_run_id"], str(run_id))
        self.assertEqual(cached_row["generated_at"], generated_at.isoformat())
        self.assertEqual(cached_row["payload_json"]["project_key"], "project-alpha")

        self.assertIsNotNone(publication_row)
        assert publication_row is not None
        self.assertEqual(publication_row["published_snapshot_set_id"], snapshot_set_id)
        self.assertEqual(publication_row["source_run_id"], run_id)
        self.assertEqual(publication_row["generated_at"], generated_at)
        self.assertEqual(publication_row["published_at"], published_at)
        self.assertEqual(result["published_snapshot_set_id"], snapshot_set_id)

    def test_publish_related_notice_snapshot_set_clears_related_notice_response_cache_on_success(self) -> None:
        organization_id = UUID("44444444-4444-4444-4444-444444444444")
        run_id = UUID("55555555-5555-5555-5555-555555555555")
        project_id = UUID("66666666-6666-6666-6666-666666666666")
        stale_snapshot_set_id = "snapshot-set-stale-001"
        generated_at = datetime(2026, 4, 8, 9, 30, tzinfo=timezone.utc)
        published_at = datetime(2026, 4, 8, 9, 31, tzinfo=timezone.utc)
        payload = {
            "run_id": str(run_id),
            "generated_at": generated_at.isoformat(),
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-1"}],
                }
            ],
        }
        stale_response = RelatedNoticeListResponse(
            project_id=project_id,
            project_name="Alpha Project",
            project_search_name="alpha project",
            status="ready",
            source="precomputed",
            message="",
            precomputed=True,
            items=[
                RelatedNoticeItem(
                    id="notice-old",
                    project_name="Alpha Project",
                    project_search_name="alpha project",
                    issuer_name="City of Seoul",
                    announce_date="20240401",
                    bid_no="R25BK00000001",
                    bid_ord="000",
                    g2b_verified="Y",
                    notice_url="",
                    notice_detail_url="",
                    match_score=144,
                    match_reason="cache",
                )
            ],
        )
        set_related_notice_response_cache(project_id, stale_response, stale_snapshot_set_id)
        self.assertIsNotNone(get_related_notice_response_cache(project_id, stale_snapshot_set_id))

        cache_repository = InMemoryRelatedNoticeCacheRepository()
        publication_repository = InMemoryRelatedNoticePublicationRepository()

        with patch(
            "backend.services.related_notice_publish_backend.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_publication_repository",
            return_value=publication_repository,
        ):
            publish_related_notice_snapshot_set_for_run(
                run_id=run_id,
                related_notice_payload=payload,
                utc_now_fn=lambda: published_at,
            )

        self.assertIsNone(get_related_notice_response_cache(project_id, stale_snapshot_set_id))

    def test_publish_related_notice_snapshot_set_clears_related_notice_response_cache_on_cas_rollover(self) -> None:
        organization_id = UUID("44444444-4444-4444-4444-444444444444")
        run_id = UUID("55555555-5555-5555-5555-555555555555")
        project_id = UUID("66666666-6666-6666-6666-666666666666")
        stale_snapshot_set_id = "snapshot-set-stale-001"
        live_snapshot_set_id = "snapshot-set-live-001"
        live_generated_at = datetime(2026, 4, 8, 8, 0, tzinfo=timezone.utc)
        live_published_at = datetime(2026, 4, 8, 8, 1, tzinfo=timezone.utc)
        candidate_generated_at = datetime(2026, 4, 8, 9, 30, tzinfo=timezone.utc)
        first_published_at = datetime(2026, 4, 8, 9, 31, tzinfo=timezone.utc)
        second_published_at = datetime(2026, 4, 8, 9, 32, tzinfo=timezone.utc)
        initial_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": live_snapshot_set_id,
            "source_run_id": UUID("77777777-7777-7777-7777-777777777777"),
            "generated_at": live_generated_at,
            "published_at": live_published_at,
            "created_at": live_generated_at,
            "updated_at": live_published_at,
        }
        candidate_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": str(run_id),
            "source_run_id": run_id,
            "generated_at": candidate_generated_at,
            "published_at": first_published_at,
            "created_at": live_generated_at,
            "updated_at": first_published_at,
        }
        republished_row = {
            **candidate_row,
            "published_at": second_published_at,
            "updated_at": second_published_at,
        }
        payload = {
            "run_id": str(run_id),
            "generated_at": candidate_generated_at.isoformat(),
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-1"}],
                }
            ],
        }
        stale_response = RelatedNoticeListResponse(
            project_id=project_id,
            project_name="Alpha Project",
            project_search_name="alpha project",
            status="ready",
            source="precomputed",
            message="stale cached response",
            precomputed=True,
            items=[
                RelatedNoticeItem(
                    id="notice-old",
                    project_name="Alpha Project",
                    project_search_name="alpha project",
                    issuer_name="City of Seoul",
                    announce_date="20240401",
                    bid_no="R25BK00000001",
                    bid_ord="000",
                    g2b_verified="Y",
                    notice_url="",
                    notice_detail_url="",
                    match_score=144,
                    match_reason="cache",
                )
            ],
        )
        set_related_notice_response_cache(project_id, stale_response, stale_snapshot_set_id)
        self.assertIsNotNone(get_related_notice_response_cache(project_id, stale_snapshot_set_id))

        class _RolloverPublicationRepository:
            def __init__(self, *, initial_row: dict[str, object], final_row: dict[str, object]) -> None:
                self._row = dict(initial_row)
                self._final_row = dict(final_row)
                self._upsert_calls = 0

            def get_publication(self, *, organization_id: UUID) -> dict[str, object] | None:
                if self._row.get("organization_id") != organization_id:
                    return None
                return dict(self._row)

            def upsert_publication_if_current(self, **kwargs: object) -> dict[str, object]:
                self._upsert_calls += 1
                if self._upsert_calls == 1:
                    return dict(self._row)
                self._row = dict(self._final_row)
                return dict(self._row)

        cache_repository = InMemoryRelatedNoticeCacheRepository()
        publication_repository = _RolloverPublicationRepository(initial_row=initial_row, final_row=republished_row)

        with patch(
            "backend.services.related_notice_publish_backend.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_publication_repository",
            return_value=publication_repository,
        ):
            result = publish_related_notice_snapshot_set_for_run(
                run_id=run_id,
                related_notice_payload=payload,
                utc_now_fn=lambda: first_published_at,
            )

        self.assertEqual(result["published_snapshot_set_id"], str(run_id))
        self.assertIsNone(get_related_notice_response_cache(project_id, stale_snapshot_set_id))

    def test_publish_related_notice_snapshot_set_restores_previous_pointer_on_publish_failure(self) -> None:
        organization_id = UUID("44444444-4444-4444-4444-444444444444")
        run_id = UUID("55555555-5555-5555-5555-555555555555")
        live_snapshot_set_id = "snapshot-set-live-001"
        live_generated_at = datetime(2026, 4, 8, 8, 0, tzinfo=timezone.utc)
        live_published_at = datetime(2026, 4, 8, 8, 1, tzinfo=timezone.utc)
        initial_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": live_snapshot_set_id,
            "source_run_id": UUID("66666666-6666-6666-6666-666666666666"),
            "generated_at": live_generated_at,
            "published_at": live_published_at,
            "created_at": live_generated_at,
            "updated_at": live_published_at,
        }
        payload = {
            "run_id": str(run_id),
            "generated_at": "2026-04-08T09:30:00+00:00",
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-1"}],
                }
            ],
        }
        cache_repository = InMemoryRelatedNoticeCacheRepository()
        publication_repository = _MutatingFailingPublicationRepository(initial_row)

        with patch(
            "backend.services.related_notice_publish_backend.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_publication_repository",
            return_value=publication_repository,
        ):
            with self.assertRaises(RuntimeError):
                publish_related_notice_snapshot_set_for_run(
                    run_id=run_id,
                    related_notice_payload=payload,
                    utc_now_fn=lambda: datetime(2026, 4, 8, 9, 31, tzinfo=timezone.utc),
                )

        restored_row = publication_repository.get_publication(organization_id=organization_id)
        self.assertIsNotNone(restored_row)
        assert restored_row is not None
        self.assertEqual(restored_row["published_snapshot_set_id"], live_snapshot_set_id)
        self.assertEqual(restored_row["source_run_id"], initial_row["source_run_id"])
        self.assertEqual(restored_row["generated_at"], live_generated_at)
        self.assertEqual(restored_row["published_at"], live_published_at)

    def test_publish_related_notice_snapshot_set_does_not_rollback_after_independent_same_candidate_publish(self) -> None:
        organization_id = UUID("44444444-4444-4444-4444-444444444444")
        run_id = UUID("55555555-5555-5555-5555-555555555555")
        live_snapshot_set_id = "snapshot-set-live-001"
        live_generated_at = datetime(2026, 4, 8, 8, 0, tzinfo=timezone.utc)
        live_published_at = datetime(2026, 4, 8, 8, 1, tzinfo=timezone.utc)
        candidate_generated_at = datetime(2026, 4, 8, 9, 30, tzinfo=timezone.utc)
        first_published_at = datetime(2026, 4, 8, 9, 31, tzinfo=timezone.utc)
        second_published_at = datetime(2026, 4, 8, 9, 32, tzinfo=timezone.utc)
        candidate_snapshot_set_id = str(run_id)
        initial_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": live_snapshot_set_id,
            "source_run_id": UUID("66666666-6666-6666-6666-666666666666"),
            "generated_at": live_generated_at,
            "published_at": live_published_at,
            "created_at": live_generated_at,
            "updated_at": live_published_at,
        }
        candidate_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": candidate_snapshot_set_id,
            "source_run_id": run_id,
            "generated_at": candidate_generated_at,
            "published_at": first_published_at,
            "created_at": live_generated_at,
            "updated_at": first_published_at,
        }
        republished_row = {
            **candidate_row,
            "published_at": second_published_at,
            "updated_at": second_published_at,
        }
        payload = {
            "run_id": str(run_id),
            "generated_at": candidate_generated_at.isoformat(),
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-1"}],
                }
            ],
        }
        cache_repository = InMemoryRelatedNoticeCacheRepository()
        publication_repository = _ConcurrentCandidatePublicationRepository(
            initial_row=initial_row,
            candidate_row=candidate_row,
            republished_row=republished_row,
        )

        with patch(
            "backend.services.related_notice_publish_backend.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_publication_repository",
            return_value=publication_repository,
        ):
            with self.assertRaises(RuntimeError):
                publish_related_notice_snapshot_set_for_run(
                    run_id=run_id,
                    related_notice_payload=payload,
                    utc_now_fn=lambda: first_published_at,
                )

        final_row = publication_repository.get_publication(organization_id=organization_id)
        self.assertIsNotNone(final_row)
        assert final_row is not None
        self.assertEqual(final_row["published_snapshot_set_id"], candidate_snapshot_set_id)
        self.assertEqual(final_row["source_run_id"], run_id)
        self.assertEqual(final_row["generated_at"], candidate_generated_at)
        self.assertEqual(final_row["published_at"], second_published_at)

    def test_precompute_related_notices_for_run_publishes_full_snapshot_set_after_success(self) -> None:
        run_repository = InMemoryRunRepository()
        stored = run_repository.create_run(
            build_phase1_run_row(
                run_type=PROJECT_TRACKER_RUN_TYPE,
                params={},
            )
        )
        run_repository.update_run(stored["id"], {"status": "success"})
        full_payload = {
            "run_id": str(stored["id"]),
            "generated_at": "2026-04-08T09:30:00+00:00",
            "projects": [
                {
                    "project_key": f"project-{index}",
                    "project_name": f"Project {index}",
                    "project_search_name": f"project {index}",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": f"notice-{index}"}],
                }
                for index in range(1, 7)
            ],
        }
        limited_payload = {
            **full_payload,
            "projects": list(full_payload["projects"][:5]),
            "project_count": 5,
            "item_count": 5,
        }
        build_calls: list[bool] = []

        def _fake_build_related_notice_artifact_payload(*, limit_projects: bool = True, **_: object) -> dict[str, object]:
            build_calls.append(limit_projects)
            return full_payload if not limit_projects else limited_payload

        artifact_repository = _RecordingArtifactRepository()

        with patch.object(run_execution, "get_run_repository", return_value=run_repository), patch.object(
            run_execution,
            "get_artifact_repository",
            return_value=artifact_repository,
        ), patch.object(run_execution, "load_seed_rows_for_run", return_value=[]), patch.object(
            run_execution,
            "_build_related_notice_artifact_payload",
            side_effect=_fake_build_related_notice_artifact_payload,
        ), patch.object(run_execution, "_upsert_related_notice_cache_entry", return_value=None), patch.object(
            run_execution,
            "_update_related_notice_summary",
            return_value=None,
        ), patch.object(
            run_execution,
            "write_json_artifact",
            return_value=SimpleNamespace(
                file_name="project_tracker_related_notices.json",
                storage_path="artifacts/project_tracker_related_notices.json",
                mime_type="application/json",
                size_bytes=1,
                checksum="abc123",
            ),
        ), patch.object(run_execution, "_log_info", return_value=None), patch.object(
            run_execution,
            "_log_warning",
            return_value=None,
        ), patch.object(run_execution, "publish_related_notice_snapshot_set_for_run") as publish_mock:
            run_execution.precompute_related_notices_for_run(UUID(str(stored["id"])))

        self.assertIn(False, build_calls)
        publish_mock.assert_called_once_with(run_id=UUID(str(stored["id"])), related_notice_payload=full_payload)

    def test_precompute_related_notices_for_run_queues_incremental_recompute_for_seed_fallback_projects(self) -> None:
        run_repository = InMemoryRunRepository()
        stored = run_repository.create_run(
            build_phase1_run_row(
                run_type=PROJECT_TRACKER_RUN_TYPE,
                params={},
            )
        )
        run_repository.update_run(stored["id"], {"status": "success"})
        payload = {
            "run_id": str(stored["id"]),
            "generated_at": "2026-04-08T09:30:00+00:00",
            "project_count": 2,
            "item_count": 2,
            "projects": [
                {
                    "project_key": "project-seed",
                    "project_name": "Seed Project",
                    "project_search_name": "seed project",
                    "issuer_name": "City of Seoul",
                    "source": "seed_fallback",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-seed"}],
                },
                {
                    "project_key": "project-live",
                    "project_name": "Live Project",
                    "project_search_name": "live project",
                    "issuer_name": "City of Seoul",
                    "source": "live",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-live"}],
                },
            ],
        }
        artifact_repository = _RecordingArtifactRepository()

        with patch.object(run_execution, "get_run_repository", return_value=run_repository), patch.object(
            run_execution,
            "get_artifact_repository",
            return_value=artifact_repository,
        ), patch.object(run_execution, "load_seed_rows_for_run", return_value=[]), patch.object(
            run_execution,
            "_build_related_notice_artifact_payload",
            return_value=payload,
        ), patch.object(run_execution, "_upsert_related_notice_cache_entry", return_value=None), patch.object(
            run_execution,
            "_update_related_notice_summary",
            return_value=None,
        ), patch.object(
            run_execution,
            "write_json_artifact",
            return_value=SimpleNamespace(
                file_name="project_tracker_related_notices.json",
                storage_path="artifacts/project_tracker_related_notices.json",
                mime_type="application/json",
                size_bytes=1,
                checksum="abc123",
            ),
        ), patch.object(run_execution, "_log_info", return_value=None), patch.object(
            run_execution,
            "_log_warning",
            return_value=None,
        ), patch.object(
            run_execution,
            "publish_related_notice_snapshot_set_for_run",
            return_value={"published_snapshot_set_id": str(stored["id"])},
        ), patch.object(run_execution, "queue_related_notice_precompute_for_run", return_value=True) as queue_mock:
            run_execution.precompute_related_notices_for_run(UUID(str(stored["id"])))

        queue_mock.assert_called_once_with(
            UUID(str(stored["id"])),
            project_key="project-seed",
            backfill_remaining=False,
            force_recompute=True,
            snapshot_set_id=str(stored["id"]),
        )

    def test_project_recompute_force_updates_current_published_snapshot_row(self) -> None:
        run_repository = InMemoryRunRepository()
        stored = run_repository.create_run(
            build_phase1_run_row(
                run_type=PROJECT_TRACKER_RUN_TYPE,
                params={},
            )
        )
        run_repository.update_run(stored["id"], {"status": "success"})
        artifact_repository = _RecordingArtifactRepository()
        artifact_repository.rows.append(
            {
                "artifact_type": "related_notices_json",
                "storage_path": "artifacts/project_tracker_related_notices.json",
            }
        )
        existing_payload = {
            "run_id": str(stored["id"]),
            "generated_at": "2026-04-08T09:00:00+00:00",
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "seed_fallback",
                    "algorithm_version": 11,
                    "items": [{"id": "seed-item"}],
                }
            ],
        }
        updated_payload = {
            "run_id": str(stored["id"]),
            "generated_at": "2026-04-08T10:00:00+00:00",
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "live",
                    "algorithm_version": 11,
                    "items": [{"id": "live-item"}],
                }
            ],
        }
        cache_repository = InMemoryRelatedNoticeCacheRepository()
        publication_repository = InMemoryRelatedNoticePublicationRepository()
        organization_id = UUID("44444444-4444-4444-4444-444444444444")
        publication_repository.upsert_publication(
            organization_id=organization_id,
            published_snapshot_set_id=str(stored["id"]),
            source_run_id=UUID(str(stored["id"])),
            generated_at="2026-04-08T09:00:00+00:00",
            published_at="2026-04-08T09:00:00+00:00",
        )

        with patch.object(run_execution, "get_run_repository", return_value=run_repository), patch.object(
            run_execution,
            "get_artifact_repository",
            return_value=artifact_repository,
        ), patch.object(run_execution, "load_seed_rows_for_run", return_value=[]), patch.object(
            run_execution,
            "_load_existing_related_notice_payload",
            return_value=existing_payload,
        ), patch.object(
            run_execution,
            "_build_related_notice_artifact_payload",
            return_value=updated_payload,
        ), patch.object(
            run_execution,
            "write_json_artifact",
            return_value=SimpleNamespace(
                file_name="project_tracker_related_notices.json",
                storage_path="artifacts/project_tracker_related_notices.json",
                mime_type="application/json",
                size_bytes=1,
                checksum="abc123",
            ),
        ), patch.object(run_execution, "_update_related_notice_summary", return_value=None), patch.object(
            run_execution,
            "_log_info",
            return_value=None,
        ), patch.object(run_execution, "_log_warning", return_value=None), patch.object(
            run_execution,
            "load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch.object(
            run_execution,
            "get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch.object(
            run_execution,
            "get_related_notice_publication_repository",
            return_value=publication_repository,
        ):
            run_execution.precompute_related_notices_for_run(
                UUID(str(stored["id"])),
                project_key="project-alpha",
                backfill_remaining=False,
                force_recompute=True,
                snapshot_set_id=str(stored["id"]),
            )

        snapshot_row = cache_repository.get_cache(project_key="project-alpha", snapshot_set_id=str(stored["id"]))
        self.assertIsNotNone(snapshot_row)
        assert snapshot_row is not None
        self.assertEqual(snapshot_row["payload_json"]["items"][0]["id"], "live-item")

    def test_precompute_related_notices_for_run_retries_publish_after_previous_failure(self) -> None:
        run_repository = InMemoryRunRepository()
        stored = run_repository.create_run(
            build_phase1_run_row(
                run_type=PROJECT_TRACKER_RUN_TYPE,
                params={},
            )
        )
        run_repository.update_run(stored["id"], {"status": "success"})
        payload = {
            "run_id": str(stored["id"]),
            "generated_at": "2026-04-08T09:30:00+00:00",
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-1"}],
                }
            ],
        }
        artifact_repository = _RecordingArtifactRepository()
        publish_results = [
            RuntimeError("publish failed during hook"),
            SimpleNamespace(published_snapshot_set_id=str(stored["id"])),
        ]

        def _fake_publish_related_notice_snapshot_set_for_run(**_: object) -> object:
            result = publish_results.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with patch.object(run_execution, "get_run_repository", return_value=run_repository), patch.object(
            run_execution,
            "get_artifact_repository",
            return_value=artifact_repository,
        ), patch.object(run_execution, "load_seed_rows_for_run", return_value=[]), patch.object(
            run_execution,
            "_build_related_notice_artifact_payload",
            return_value=payload,
        ), patch.object(run_execution, "_upsert_related_notice_cache_entry", return_value=None), patch.object(
            run_execution,
            "_update_related_notice_summary",
            return_value=None,
        ), patch.object(
            run_execution,
            "write_json_artifact",
            return_value=SimpleNamespace(
                file_name="project_tracker_related_notices.json",
                storage_path="artifacts/project_tracker_related_notices.json",
                mime_type="application/json",
                size_bytes=1,
                checksum="abc123",
            ),
        ), patch.object(run_execution, "_log_info", return_value=None), patch.object(
            run_execution,
            "_log_warning",
            return_value=None,
        ), patch.object(
            run_execution,
            "publish_related_notice_snapshot_set_for_run",
            side_effect=_fake_publish_related_notice_snapshot_set_for_run,
        ):
            run_execution.precompute_related_notices_for_run(UUID(str(stored["id"])))
            run_execution.precompute_related_notices_for_run(UUID(str(stored["id"])))

        self.assertEqual(len(publish_results), 0)

    def test_publish_related_notice_snapshot_set_refuses_older_candidate_when_newer_publication_exists(self) -> None:
        organization_id = UUID("44444444-4444-4444-4444-444444444444")
        run_id = UUID("55555555-5555-5555-5555-555555555555")
        older_generated_at = datetime(2026, 4, 8, 7, 0, tzinfo=timezone.utc)
        newer_generated_at = datetime(2026, 4, 8, 8, 30, tzinfo=timezone.utc)
        cache_repository = InMemoryRelatedNoticeCacheRepository()
        live_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": "snapshot-set-live-002",
            "source_run_id": UUID("66666666-6666-6666-6666-666666666666"),
            "generated_at": newer_generated_at,
            "published_at": newer_generated_at,
            "created_at": newer_generated_at,
            "updated_at": newer_generated_at,
        }
        payload = {
            "run_id": str(run_id),
            "generated_at": older_generated_at.isoformat(),
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-1"}],
                }
            ],
        }
        publication_repo = SimpleNamespace(
            get_publication=lambda *, organization_id: dict(live_row) if organization_id == live_row["organization_id"] else None,
            upsert_publication=Mock(side_effect=AssertionError("older publication should not cut over")),
        )

        with patch(
            "backend.services.related_notice_publish_backend.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_publication_repository",
            return_value=publication_repo,
        ):
            result = publish_related_notice_snapshot_set_for_run(
                run_id=run_id,
                related_notice_payload=payload,
                utc_now_fn=lambda: older_generated_at,
            )

        self.assertEqual(result["published_snapshot_set_id"], live_row["published_snapshot_set_id"])
        publication_repo.upsert_publication.assert_not_called()

    def test_publish_related_notice_snapshot_set_refuses_racy_stale_overwrite_after_read(self) -> None:
        organization_id = UUID("44444444-4444-4444-4444-444444444444")
        run_id = UUID("55555555-5555-5555-5555-555555555555")
        previous_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": "snapshot-set-live-001",
            "source_run_id": UUID("66666666-6666-6666-6666-666666666666"),
            "generated_at": datetime(2026, 4, 8, 6, 0, tzinfo=timezone.utc),
            "published_at": datetime(2026, 4, 8, 6, 1, tzinfo=timezone.utc),
            "created_at": datetime(2026, 4, 8, 6, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 4, 8, 6, 1, tzinfo=timezone.utc),
        }
        raced_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": "snapshot-set-live-002",
            "source_run_id": UUID("77777777-7777-7777-7777-777777777777"),
            "generated_at": datetime(2026, 4, 8, 8, 30, tzinfo=timezone.utc),
            "published_at": datetime(2026, 4, 8, 8, 31, tzinfo=timezone.utc),
            "created_at": datetime(2026, 4, 8, 8, 30, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 4, 8, 8, 31, tzinfo=timezone.utc),
        }
        payload = {
            "run_id": str(run_id),
            "generated_at": datetime(2026, 4, 8, 7, 0, tzinfo=timezone.utc).isoformat(),
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-1"}],
                }
            ],
        }
        cache_repository = InMemoryRelatedNoticeCacheRepository()
        publication_repository = _RacingPublicationRepository(initial_row=previous_row, raced_row=raced_row)

        with patch(
            "backend.services.related_notice_publish_backend.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_publication_repository",
            return_value=publication_repository,
        ):
            result = publish_related_notice_snapshot_set_for_run(
                run_id=run_id,
                related_notice_payload=payload,
                utc_now_fn=lambda: datetime(2026, 4, 8, 7, 1, tzinfo=timezone.utc),
            )

        self.assertEqual(result["published_snapshot_set_id"], "snapshot-set-live-002")
        self.assertEqual(
            publication_repository.get_publication(organization_id=organization_id)["published_snapshot_set_id"],
            "snapshot-set-live-002",
        )

    def test_publish_related_notice_snapshot_set_recovers_newer_candidate_after_cas_miss(self) -> None:
        organization_id = UUID("44444444-4444-4444-4444-444444444444")
        run_id = UUID("55555555-5555-5555-5555-555555555555")
        previous_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": "snapshot-set-live-001",
            "source_run_id": UUID("66666666-6666-6666-6666-666666666666"),
            "generated_at": datetime(2026, 4, 8, 6, 0, tzinfo=timezone.utc),
            "published_at": datetime(2026, 4, 8, 6, 1, tzinfo=timezone.utc),
            "created_at": datetime(2026, 4, 8, 6, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 4, 8, 6, 1, tzinfo=timezone.utc),
        }
        raced_row = {
            "organization_id": organization_id,
            "published_snapshot_set_id": "snapshot-set-live-002",
            "source_run_id": UUID("77777777-7777-7777-7777-777777777777"),
            "generated_at": datetime(2026, 4, 8, 8, 30, tzinfo=timezone.utc),
            "published_at": datetime(2026, 4, 8, 8, 31, tzinfo=timezone.utc),
            "created_at": datetime(2026, 4, 8, 8, 30, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 4, 8, 8, 31, tzinfo=timezone.utc),
        }
        payload = {
            "run_id": str(run_id),
            "generated_at": datetime(2026, 4, 8, 9, 30, tzinfo=timezone.utc).isoformat(),
            "projects": [
                {
                    "project_key": "project-alpha",
                    "project_name": "Alpha Project",
                    "project_search_name": "alpha project",
                    "issuer_name": "City of Seoul",
                    "source": "precomputed",
                    "algorithm_version": 11,
                    "items": [{"id": "notice-1"}],
                }
            ],
        }
        cache_repository = InMemoryRelatedNoticeCacheRepository()
        publication_repository = _RacingPublicationRepository(initial_row=previous_row, raced_row=raced_row)

        with patch(
            "backend.services.related_notice_publish_backend.load_phase1_identity",
            return_value=SimpleNamespace(organization_id=organization_id),
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_cache_repository",
            return_value=cache_repository,
        ), patch(
            "backend.services.related_notice_publish_backend.get_related_notice_publication_repository",
            return_value=publication_repository,
        ):
            result = publish_related_notice_snapshot_set_for_run(
                run_id=run_id,
                related_notice_payload=payload,
                utc_now_fn=lambda: datetime(2026, 4, 8, 9, 31, tzinfo=timezone.utc),
            )

        self.assertEqual(result["published_snapshot_set_id"], str(run_id))
        final_row = publication_repository.get_publication(organization_id=organization_id)
        self.assertIsNotNone(final_row)
        assert final_row is not None
        self.assertEqual(final_row["published_snapshot_set_id"], str(run_id))
        self.assertEqual(final_row["source_run_id"], run_id)
        self.assertEqual(final_row["generated_at"], datetime(2026, 4, 8, 9, 30, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
