from __future__ import annotations

import os
from functools import lru_cache

from .artifacts import ArtifactRepository
from .artifacts import ArtifactRepositoryConfigError
from .download_audit_logs import DownloadAuditLogRepository
from .download_audit_logs import DownloadAuditLogRepositoryConfigError
from .in_memory_login_audit_logs import InMemoryLoginAuditLogRepository
from .in_memory_artifacts import InMemoryArtifactRepository
from .in_memory_backfill_conflicts import InMemoryBackfillConflictRepository
from .in_memory_download_audit_logs import InMemoryDownloadAuditLogRepository
from .in_memory_home_bootstrap_snapshots import InMemoryHomeBootstrapSnapshotRepository
from .in_memory_tracker_change_events import InMemoryTrackerChangeEventRepository
from .in_memory_logs import InMemoryRunLogRepository
from .in_memory_related_notice_cache import InMemoryRelatedNoticeCacheRepository
from .in_memory_related_notice_publications import InMemoryRelatedNoticePublicationRepository
from .in_memory_runs import InMemoryRunRepository
from .in_memory_sales_claims import InMemorySalesClaimRepository
from .in_memory_tracker_entry_snapshots import InMemoryTrackerEntrySnapshotRepository
from .in_memory_tracker_entries import InMemoryTrackerEntryRepository
from .logs import RunLogRepository
from .logs import RunLogRepositoryConfigError
from .related_notice_cache import RelatedNoticeCacheRepository
from .related_notice_cache import RelatedNoticeCacheRepositoryConfigError
from .related_notice_publications import RelatedNoticePublicationRepository
from .related_notice_publications import RelatedNoticePublicationRepositoryConfigError
from .runs import RunRepository
from .runs import RunRepositoryConfigError
from .sales_claims import SalesClaimRepository
from .sales_claims import SalesClaimRepositoryConfigError
from .sqlite_artifacts import SqliteArtifactRepository
from .sqlite_download_audit_logs import SqliteDownloadAuditLogRepository
from .sqlite_login_audit_logs import SqliteLoginAuditLogRepository
from .sqlite_logs import SqliteRunLogRepository
from .sqlite_runs import SqliteRunRepository
from .home_bootstrap_snapshots import HomeBootstrapSnapshotRepository
from .home_bootstrap_snapshots import HomeBootstrapSnapshotRepositoryConfigError
from .supabase_backfill_conflicts import SupabaseBackfillConflictRepository
from .supabase_backfill_conflicts import SupabaseBackfillConflictRepositoryConfig
from .supabase_artifacts import SupabaseArtifactRepository
from .supabase_artifacts import SupabaseArtifactRepositoryConfig
from .supabase_logs import SupabaseRunLogRepository
from .supabase_logs import SupabaseRunLogRepositoryConfig
from .supabase_related_notice_cache import SupabaseRelatedNoticeCacheRepository
from .supabase_related_notice_cache import SupabaseRelatedNoticeCacheRepositoryConfig
from .supabase_related_notice_publications import SupabaseRelatedNoticePublicationRepository
from .supabase_related_notice_publications import SupabaseRelatedNoticePublicationRepositoryConfig
from .supabase_home_bootstrap_snapshots import SupabaseHomeBootstrapSnapshotRepository
from .supabase_home_bootstrap_snapshots import SupabaseHomeBootstrapSnapshotRepositoryConfig
from .supabase_sales_claims import SupabaseSalesClaimRepository
from .supabase_sales_claims import SupabaseSalesClaimRepositoryConfig
from .supabase_download_audit_logs import SupabaseDownloadAuditLogRepository
from .supabase_download_audit_logs import SupabaseDownloadAuditLogRepositoryConfig
from .supabase_login_audit_logs import SupabaseLoginAuditLogRepository
from .supabase_login_audit_logs import SupabaseLoginAuditLogRepositoryConfig
from .supabase_tracker_entry_snapshots import SupabaseTrackerEntrySnapshotRepository
from .supabase_tracker_entry_snapshots import SupabaseTrackerEntrySnapshotRepositoryConfig
from .supabase_tracker_change_events import SupabaseTrackerChangeEventRepository
from .supabase_tracker_change_events import SupabaseTrackerChangeEventRepositoryConfig
from .supabase_tracker_entries import SupabaseTrackerEntryRepository
from .supabase_tracker_entries import SupabaseTrackerEntryRepositoryConfig
from .supabase_runs import SupabaseRunRepository
from .supabase_runs import SupabaseRunRepositoryConfig
from .tracker_entries import TrackerEntryRepository
from .tracker_entries import TrackerEntryRepositoryConfigError
from .tracker_change_events import TrackerChangeEventRepository
from .tracker_change_events import TrackerChangeEventRepositoryConfigError
from .tracker_entry_snapshots import TrackerEntrySnapshotRepository
from .tracker_entry_snapshots import TrackerEntrySnapshotRepositoryConfigError
from .backfill_conflicts import BackfillConflictRepository
from .backfill_conflicts import BackfillConflictRepositoryConfigError
from .login_audit_logs import LoginAuditLogRepository
from .login_audit_logs import LoginAuditLogRepositoryConfigError

VALID_REPOSITORY_BACKENDS = frozenset({"in_memory", "sqlite", "supabase", "postgres", "postgrest"})


def _has_supabase_configuration() -> bool:
    base_url = os.getenv("SUPABASE_URL", "").strip()
    api_key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SECRET", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    return bool(base_url and api_key)


def _default_backend() -> str:
    if _has_supabase_configuration():
        return "supabase"
    return "in_memory"


def _resolve_backend(*env_names: str) -> str:
    for env_name in env_names:
        raw = os.getenv(env_name, "").strip().lower()
        if not raw or raw == "auto":
            continue
        return raw
    return _default_backend()


def _resolve_backend_without_sqlite_fallback(primary_env_name: str, *fallback_env_names: str) -> str:
    raw = os.getenv(primary_env_name, "").strip().lower()
    if raw and raw != "auto":
        return raw
    for env_name in fallback_env_names:
        raw = os.getenv(env_name, "").strip().lower()
        if not raw or raw == "auto" or raw == "sqlite":
            continue
        return raw
    return _default_backend()


def _validate_backend(name: str, *, error_cls: type[Exception], env_label: str) -> str:
    if name in VALID_REPOSITORY_BACKENDS:
        return name
    allowed = ", ".join(sorted((*VALID_REPOSITORY_BACKENDS, "auto")))
    raise error_cls(f"{env_label} must be one of {allowed}")


def _raise_sqlite_unsupported(*, error_cls: type[Exception], repository_name: str, env_label: str) -> None:
    raise error_cls(
        f"sqlite backend is not implemented for {repository_name}; set {env_label} to in_memory, supabase, "
        "postgres, or postgrest"
    )


def describe_repository_backends() -> dict[str, str | bool]:
    tracker_backend = _validate_backend(
        _resolve_backend("TRACKER_REPOSITORY_BACKEND"),
        error_cls=TrackerEntryRepositoryConfigError,
        env_label="TRACKER_REPOSITORY_BACKEND",
    )
    run_backend = _validate_backend(
        _resolve_backend("RUN_REPOSITORY_BACKEND", "TRACKER_REPOSITORY_BACKEND"),
        error_cls=RunRepositoryConfigError,
        env_label="RUN_REPOSITORY_BACKEND",
    )
    artifact_backend = _validate_backend(
        _resolve_backend("ARTIFACT_REPOSITORY_BACKEND", "RUN_REPOSITORY_BACKEND", "TRACKER_REPOSITORY_BACKEND"),
        error_cls=ArtifactRepositoryConfigError,
        env_label="ARTIFACT_REPOSITORY_BACKEND",
    )
    log_backend = _validate_backend(
        _resolve_backend("RUN_LOG_REPOSITORY_BACKEND", "RUN_REPOSITORY_BACKEND", "TRACKER_REPOSITORY_BACKEND"),
        error_cls=RunLogRepositoryConfigError,
        env_label="RUN_LOG_REPOSITORY_BACKEND",
    )
    related_notice_cache_backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "RELATED_NOTICE_CACHE_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=RelatedNoticeCacheRepositoryConfigError,
        env_label="RELATED_NOTICE_CACHE_REPOSITORY_BACKEND",
    )
    related_notice_publication_backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=RelatedNoticePublicationRepositoryConfigError,
        env_label="RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND",
    )
    sales_claim_backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "SALES_CLAIM_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=SalesClaimRepositoryConfigError,
        env_label="SALES_CLAIM_REPOSITORY_BACKEND",
    )
    download_audit_log_backend = _validate_backend(
        _resolve_backend(
            "DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=DownloadAuditLogRepositoryConfigError,
        env_label="DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND",
    )
    login_audit_log_backend = _validate_backend(
        _resolve_backend(
            "LOGIN_AUDIT_LOG_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=LoginAuditLogRepositoryConfigError,
        env_label="LOGIN_AUDIT_LOG_REPOSITORY_BACKEND",
    )
    tracker_snapshot_backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=TrackerEntrySnapshotRepositoryConfigError,
        env_label="TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND",
    )
    home_bootstrap_snapshot_backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=HomeBootstrapSnapshotRepositoryConfigError,
        env_label="HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND",
    )
    return {
        "tracker_entries": tracker_backend,
        "tracker_entry_snapshots": tracker_snapshot_backend,
        "home_bootstrap_snapshots": home_bootstrap_snapshot_backend,
        "runs": run_backend,
        "artifacts": artifact_backend,
        "logs": log_backend,
        "related_notice_cache": related_notice_cache_backend,
        "related_notice_publications": related_notice_publication_backend,
        "sales_claims": sales_claim_backend,
        "download_audit_logs": download_audit_log_backend,
        "login_audit_logs": login_audit_log_backend,
        "artifact_metadata_persistent": artifact_backend != "in_memory",
    }


@lru_cache(maxsize=1)
def get_tracker_entry_repository() -> TrackerEntryRepository:
    backend = _validate_backend(
        _resolve_backend("TRACKER_REPOSITORY_BACKEND"),
        error_cls=TrackerEntryRepositoryConfigError,
        env_label="TRACKER_REPOSITORY_BACKEND",
    )

    if backend == "in_memory":
        return InMemoryTrackerEntryRepository()
    if backend == "sqlite":
        _raise_sqlite_unsupported(
            error_cls=TrackerEntryRepositoryConfigError,
            repository_name="tracker_entries",
            env_label="TRACKER_REPOSITORY_BACKEND",
        )
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseTrackerEntryRepository(SupabaseTrackerEntryRepositoryConfig.from_env())

    raise AssertionError(f"unsupported tracker backend: {backend}")


@lru_cache(maxsize=1)
def get_run_repository() -> RunRepository:
    backend = _validate_backend(
        _resolve_backend("RUN_REPOSITORY_BACKEND", "TRACKER_REPOSITORY_BACKEND"),
        error_cls=RunRepositoryConfigError,
        env_label="RUN_REPOSITORY_BACKEND",
    )

    if backend == "in_memory":
        return InMemoryRunRepository()
    if backend == "sqlite":
        return SqliteRunRepository()
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseRunRepository(SupabaseRunRepositoryConfig.from_env())

    raise AssertionError(f"unsupported run backend: {backend}")


@lru_cache(maxsize=1)
def get_artifact_repository() -> ArtifactRepository:
    backend = _validate_backend(
        _resolve_backend("ARTIFACT_REPOSITORY_BACKEND", "RUN_REPOSITORY_BACKEND", "TRACKER_REPOSITORY_BACKEND"),
        error_cls=ArtifactRepositoryConfigError,
        env_label="ARTIFACT_REPOSITORY_BACKEND",
    )

    if backend == "in_memory":
        return InMemoryArtifactRepository()
    if backend == "sqlite":
        return SqliteArtifactRepository()
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseArtifactRepository(SupabaseArtifactRepositoryConfig.from_env())

    raise AssertionError(f"unsupported artifact backend: {backend}")


@lru_cache(maxsize=1)
def get_run_log_repository() -> RunLogRepository:
    backend = _validate_backend(
        _resolve_backend("RUN_LOG_REPOSITORY_BACKEND", "RUN_REPOSITORY_BACKEND", "TRACKER_REPOSITORY_BACKEND"),
        error_cls=RunLogRepositoryConfigError,
        env_label="RUN_LOG_REPOSITORY_BACKEND",
    )

    if backend == "in_memory":
        return InMemoryRunLogRepository()
    if backend == "sqlite":
        return SqliteRunLogRepository()
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseRunLogRepository(SupabaseRunLogRepositoryConfig.from_env())

    raise AssertionError(f"unsupported run log backend: {backend}")


@lru_cache(maxsize=1)
def get_related_notice_cache_repository() -> RelatedNoticeCacheRepository:
    backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "RELATED_NOTICE_CACHE_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=RelatedNoticeCacheRepositoryConfigError,
        env_label="RELATED_NOTICE_CACHE_REPOSITORY_BACKEND",
    )

    if backend == "in_memory":
        return InMemoryRelatedNoticeCacheRepository()
    if backend == "sqlite":
        _raise_sqlite_unsupported(
            error_cls=RelatedNoticeCacheRepositoryConfigError,
            repository_name="related_notice_cache",
            env_label="RELATED_NOTICE_CACHE_REPOSITORY_BACKEND",
        )
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseRelatedNoticeCacheRepository(SupabaseRelatedNoticeCacheRepositoryConfig.from_env())

    raise AssertionError(f"unsupported related notice cache backend: {backend}")


@lru_cache(maxsize=1)
def get_related_notice_publication_repository() -> RelatedNoticePublicationRepository:
    backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=RelatedNoticePublicationRepositoryConfigError,
        env_label="RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND",
    )

    if backend == "in_memory":
        return InMemoryRelatedNoticePublicationRepository()
    if backend == "sqlite":
        _raise_sqlite_unsupported(
            error_cls=RelatedNoticePublicationRepositoryConfigError,
            repository_name="related_notice_publications",
            env_label="RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND",
        )
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseRelatedNoticePublicationRepository(SupabaseRelatedNoticePublicationRepositoryConfig.from_env())

    raise AssertionError(f"unsupported related notice publication backend: {backend}")


@lru_cache(maxsize=1)
def get_sales_claim_repository() -> SalesClaimRepository:
    backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "SALES_CLAIM_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=SalesClaimRepositoryConfigError,
        env_label="SALES_CLAIM_REPOSITORY_BACKEND",
    )

    if backend == "in_memory":
        return InMemorySalesClaimRepository()
    if backend == "sqlite":
        _raise_sqlite_unsupported(
            error_cls=SalesClaimRepositoryConfigError,
            repository_name="sales_claims",
            env_label="SALES_CLAIM_REPOSITORY_BACKEND",
        )
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseSalesClaimRepository(SupabaseSalesClaimRepositoryConfig.from_env())

    raise AssertionError(f"unsupported sales claim backend: {backend}")


@lru_cache(maxsize=1)
def get_download_audit_log_repository() -> DownloadAuditLogRepository:
    backend = _validate_backend(
        _resolve_backend(
            "DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=DownloadAuditLogRepositoryConfigError,
        env_label="DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND",
    )

    if backend == "in_memory":
        return InMemoryDownloadAuditLogRepository()
    if backend == "sqlite":
        return SqliteDownloadAuditLogRepository()
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseDownloadAuditLogRepository(SupabaseDownloadAuditLogRepositoryConfig.from_env())

    raise AssertionError(f"unsupported download audit log backend: {backend}")


@lru_cache(maxsize=1)
def get_login_audit_log_repository() -> LoginAuditLogRepository:
    backend = _validate_backend(
        _resolve_backend(
            "LOGIN_AUDIT_LOG_REPOSITORY_BACKEND",
            "RUN_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=LoginAuditLogRepositoryConfigError,
        env_label="LOGIN_AUDIT_LOG_REPOSITORY_BACKEND",
    )

    if backend == "in_memory":
        return InMemoryLoginAuditLogRepository()
    if backend == "sqlite":
        return SqliteLoginAuditLogRepository()
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseLoginAuditLogRepository(SupabaseLoginAuditLogRepositoryConfig.from_env())

    raise AssertionError(f"unsupported login audit log backend: {backend}")


@lru_cache(maxsize=1)
def get_tracker_change_event_repository() -> TrackerChangeEventRepository:
    backend = _validate_backend(
        _resolve_backend(
            "TRACKER_CHANGE_EVENT_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=TrackerChangeEventRepositoryConfigError,
        env_label="TRACKER_CHANGE_EVENT_REPOSITORY_BACKEND",
    )
    if backend == "in_memory":
        return InMemoryTrackerChangeEventRepository()
    if backend == "sqlite":
        _raise_sqlite_unsupported(
            error_cls=TrackerChangeEventRepositoryConfigError,
            repository_name="tracker_change_events",
            env_label="TRACKER_CHANGE_EVENT_REPOSITORY_BACKEND",
        )
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseTrackerChangeEventRepository(SupabaseTrackerChangeEventRepositoryConfig.from_env())
    raise AssertionError(f"unsupported tracker change event backend: {backend}")


@lru_cache(maxsize=1)
def get_tracker_entry_snapshot_repository() -> TrackerEntrySnapshotRepository:
    backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=TrackerEntrySnapshotRepositoryConfigError,
        env_label="TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND",
    )
    if backend == "in_memory":
        return InMemoryTrackerEntrySnapshotRepository()
    if backend == "sqlite":
        _raise_sqlite_unsupported(
            error_cls=TrackerEntrySnapshotRepositoryConfigError,
            repository_name="tracker_entry_snapshots",
            env_label="TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND",
        )
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseTrackerEntrySnapshotRepository(SupabaseTrackerEntrySnapshotRepositoryConfig.from_env())
    raise AssertionError(f"unsupported tracker entry snapshot backend: {backend}")


@lru_cache(maxsize=1)
def get_home_bootstrap_snapshot_repository() -> HomeBootstrapSnapshotRepository:
    backend = _validate_backend(
        _resolve_backend_without_sqlite_fallback(
            "HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=HomeBootstrapSnapshotRepositoryConfigError,
        env_label="HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND",
    )
    if backend == "in_memory":
        return InMemoryHomeBootstrapSnapshotRepository()
    if backend == "sqlite":
        _raise_sqlite_unsupported(
            error_cls=HomeBootstrapSnapshotRepositoryConfigError,
            repository_name="home_bootstrap_snapshots",
            env_label="HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND",
        )
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseHomeBootstrapSnapshotRepository(SupabaseHomeBootstrapSnapshotRepositoryConfig.from_env())
    raise AssertionError(f"unsupported home bootstrap snapshot backend: {backend}")


@lru_cache(maxsize=1)
def get_backfill_conflict_repository() -> BackfillConflictRepository:
    backend = _validate_backend(
        _resolve_backend(
            "BACKFILL_CONFLICT_REPOSITORY_BACKEND",
            "TRACKER_REPOSITORY_BACKEND",
        ),
        error_cls=BackfillConflictRepositoryConfigError,
        env_label="BACKFILL_CONFLICT_REPOSITORY_BACKEND",
    )
    if backend == "in_memory":
        return InMemoryBackfillConflictRepository()
    if backend == "sqlite":
        _raise_sqlite_unsupported(
            error_cls=BackfillConflictRepositoryConfigError,
            repository_name="backfill_conflicts",
            env_label="BACKFILL_CONFLICT_REPOSITORY_BACKEND",
        )
    if backend in {"supabase", "postgres", "postgrest"}:
        return SupabaseBackfillConflictRepository(SupabaseBackfillConflictRepositoryConfig.from_env())
    raise AssertionError(f"unsupported backfill conflict backend: {backend}")


def reset_tracker_entry_repository() -> None:
    get_tracker_entry_repository.cache_clear()


def reset_run_repository() -> None:
    get_run_repository.cache_clear()


def reset_artifact_repository() -> None:
    get_artifact_repository.cache_clear()


def reset_run_log_repository() -> None:
    get_run_log_repository.cache_clear()


def reset_related_notice_cache_repository() -> None:
    get_related_notice_cache_repository.cache_clear()


def reset_related_notice_publication_repository() -> None:
    get_related_notice_publication_repository.cache_clear()


def reset_sales_claim_repository() -> None:
    get_sales_claim_repository.cache_clear()


def reset_tracker_change_event_repository() -> None:
    get_tracker_change_event_repository.cache_clear()


def reset_download_audit_log_repository() -> None:
    get_download_audit_log_repository.cache_clear()


def reset_login_audit_log_repository() -> None:
    get_login_audit_log_repository.cache_clear()


def reset_backfill_conflict_repository() -> None:
    get_backfill_conflict_repository.cache_clear()


def reset_tracker_entry_snapshot_repository() -> None:
    get_tracker_entry_snapshot_repository.cache_clear()


def reset_home_bootstrap_snapshot_repository() -> None:
    get_home_bootstrap_snapshot_repository.cache_clear()
