from __future__ import annotations

import unittest

from fastapi import APIRouter


class ApiRouterRegistrationTests(unittest.TestCase):
    def test_app_module_exposes_router_modules(self) -> None:
        from backend.api.routers import auth
        from backend.api.routers import admin
        from backend.api.routers import artifacts
        from backend.api.routers import core
        from backend.api.routers import reports
        from backend.api.routers import runs
        from backend.api.routers import backfill_conflicts
        from backend.api.routers import sales_claims
        from backend.api.routers import tracker

        self.assertIsInstance(auth.router, APIRouter)
        self.assertIsInstance(admin.router, APIRouter)
        self.assertIsInstance(artifacts.router, APIRouter)
        self.assertIsInstance(backfill_conflicts.router, APIRouter)
        self.assertIsInstance(core.router, APIRouter)
        self.assertIsInstance(reports.router, APIRouter)
        self.assertIsInstance(runs.router, APIRouter)
        self.assertIsInstance(sales_claims.router, APIRouter)
        self.assertIsInstance(tracker.router, APIRouter)

    def test_app_includes_baseline_routes(self) -> None:
        from backend.api.app import app

        paths = {route.path for route in app.routes}

        self.assertIn("/api/auth/sign-in", paths)
        self.assertIn("/api/admin/accounts", paths)
        self.assertIn("/api/artifacts/{artifact_id}/download", paths)
        self.assertIn("/api/artifacts/{artifact_id}/preview", paths)
        self.assertIn("/api/backfill-conflicts", paths)
        self.assertIn("/api/backfill-conflicts/{conflict_id}/resolve", paths)
        self.assertIn("/api/dashboard/summary", paths)
        self.assertIn("/api/report-jobs", paths)
        self.assertIn("/api/report-jobs/{job_id}", paths)
        self.assertIn("/api/reports/{report_name}", paths)
        self.assertIn("/api/run-presets", paths)
        self.assertIn("/api/runs", paths)
        self.assertIn("/api/runs/{run_id}", paths)
        self.assertIn("/api/runs/{run_id}/artifacts", paths)
        self.assertIn("/api/runs/{run_id}/cancel", paths)
        self.assertIn("/api/runs/{run_id}/events", paths)
        self.assertIn("/api/runs/{run_id}/logs", paths)
        self.assertIn("/api/home-bootstrap", paths)
        self.assertIn("/api/sales-claims", paths)
        self.assertIn("/api/sales-claims/action-recommendations", paths)
        self.assertIn("/api/sales-claims/overview", paths)
        self.assertIn("/api/sales-claims/export", paths)
        self.assertIn("/api/sales-claims/projects/{project_id}/claim", paths)
        self.assertIn("/api/sales-claims/projects/{project_id}", paths)
        self.assertIn("/api/sales-claims/projects/{project_id}/transfer", paths)
        self.assertIn("/api/sales-claims/projects/{project_id}/close", paths)
        self.assertIn("/api/sales-claims/projects/{project_id}/release", paths)
        self.assertIn("/api/sales-claims/summary-by-user", paths)
        self.assertIn("/api/projects", paths)
        self.assertIn("/api/tracker-entry-summaries/download", paths)
        self.assertIn("/api/tracker-entry-summaries", paths)
        self.assertIn("/api/tracker-template", paths)
        self.assertIn("/api/tracker-entries", paths)
        self.assertIn("/api/tracker-entries/{entry_id}", paths)
        self.assertIn("/api/tracker-change-events", paths)
        self.assertIn("/health", paths)
        self.assertIn("/", paths)
        self.assertIn("/app", paths)

    def _assert_route_is_owned_by_module(self, routes, method: str, path: str, module_name: str) -> None:
        matching_routes = [
            route
            for route in routes
            if getattr(route, "path", None) == path and method in getattr(route, "methods", set())
        ]

        self.assertEqual(
            len(matching_routes),
            1,
            msg=f"expected exactly one route for {method} {path}, found {len(matching_routes)}",
        )
        self.assertEqual(matching_routes[0].endpoint.__module__, module_name)

    def test_artifacts_router_owns_artifact_paths(self) -> None:
        from backend.api.routers import artifacts

        artifact_paths = {route.path for route in artifacts.router.routes}

        self.assertIn("/api/artifacts/{artifact_id}/download", artifact_paths)
        self.assertIn("/api/artifacts/{artifact_id}/preview", artifact_paths)

    def test_auth_router_owns_auth_paths(self) -> None:
        from backend.api.routers import auth

        auth_paths = {route.path for route in auth.router.routes}

        self.assertIn("/api/auth/sign-in", auth_paths)
        self.assertIn("/api/auth/session", auth_paths)
        self.assertIn("/api/auth/profile", auth_paths)

    def test_admin_router_owns_admin_paths(self) -> None:
        from backend.api.app import app
        from backend.api.routers import admin

        admin_paths = {route.path for route in admin.router.routes}

        self.assertIn("/api/admin/accounts", admin_paths)
        self.assertIn("/api/admin/accounts/{user_id}/password-reset", admin_paths)
        self.assertNotIn("/api/admin/google-sheets/bootstrap", admin_paths)
        self.assertNotIn("/api/admin/google-sheets/sheets/{sheet_key}", admin_paths)
        self.assertNotIn("/api/admin/google-sheets/sync", admin_paths)

    def test_backfill_conflicts_router_owns_backfill_conflict_paths(self) -> None:
        from backend.api.app import app
        from backend.api.routers import backfill_conflicts

        expected_routes = {
            ("GET", "/api/backfill-conflicts"),
            ("POST", "/api/backfill-conflicts/{conflict_id}/resolve"),
        }

        backfill_conflicts_routes = {
            (next(iter(route.methods - {"HEAD", "OPTIONS"})), route.path)
            for route in backfill_conflicts.router.routes
        }

        self.assertEqual(backfill_conflicts_routes, expected_routes)
        for method, path in expected_routes:
            self._assert_route_is_owned_by_module(app.routes, method, path, "backend.api.routers.backfill_conflicts")

    def test_related_notice_routes_are_removed(self) -> None:
        from backend.api.app import app

        paths = {route.path for route in app.routes}

        self.assertNotIn("/api/projects/{project_id}/related-notices", paths)
        self.assertNotIn("/api/projects/{project_id}/related-notices/progress", paths)
        self.assertNotIn("/api/projects/{project_id}/related-notices/recompute", paths)
        self.assertNotIn("/api/projects/{project_id}/notice-view", paths)
        self.assertNotIn("/api/notices/view", paths)

    def test_core_router_owns_dashboard_and_project_paths(self) -> None:
        from backend.api.app import app
        from backend.api.routers import core

        expected_routes = {
            ("GET", "/api/dashboard/summary"),
            ("GET", "/api/projects"),
        }

        core_routes = {
            (next(iter(route.methods - {"HEAD", "OPTIONS"})), route.path)
            for route in core.router.routes
        }

        self.assertEqual(core_routes, expected_routes)
        for method, path in expected_routes:
            self._assert_route_is_owned_by_module(app.routes, method, path, "backend.api.routers.core")

    def test_app_keeps_shell_routes_in_app_module(self) -> None:
        from backend.api.app import app

        self._assert_route_is_owned_by_module(app.routes, "GET", "/health", "backend.api.app")
        self._assert_route_is_owned_by_module(app.routes, "GET", "/", "backend.api.app")
        self._assert_route_is_owned_by_module(app.routes, "GET", "/app", "backend.api.app")

    def test_sales_claims_router_owns_sales_claim_paths(self) -> None:
        from backend.api.app import app
        from backend.api.routers import sales_claims

        expected_routes = {
            ("GET", "/api/sales-claims"),
            ("GET", "/api/sales-claims/action-recommendations"),
            ("GET", "/api/sales-claims/overview"),
            ("GET", "/api/sales-claims/export"),
            ("POST", "/api/sales-claims/projects/{project_id}/claim"),
            ("PATCH", "/api/sales-claims/projects/{project_id}"),
            ("POST", "/api/sales-claims/projects/{project_id}/transfer"),
            ("POST", "/api/sales-claims/projects/{project_id}/close"),
            ("POST", "/api/sales-claims/projects/{project_id}/release"),
            ("GET", "/api/sales-claims/summary-by-user"),
        }

        sales_claims_routes = {
            (next(iter(route.methods - {"HEAD", "OPTIONS"})), route.path)
            for route in sales_claims.router.routes
        }

        self.assertEqual(sales_claims_routes, expected_routes)
        for method, path in expected_routes:
            self._assert_route_is_owned_by_module(app.routes, method, path, "backend.api.routers.sales_claims")

    def test_tracker_router_owns_tracker_paths(self) -> None:
        from backend.api.app import app
        from backend.api.routers import tracker

        expected_routes = {
            ("POST", "/api/runs/{run_id}/tracker-export"),
            ("GET", "/api/home-bootstrap"),
            ("GET", "/api/tracker-entry-summaries"),
            ("GET", "/api/tracker-entry-summaries/download"),
            ("POST", "/api/tracker-entry-summaries/download-jobs"),
            ("GET", "/api/tracker-entry-summaries/download-jobs/{job_id}"),
            ("GET", "/api/tracker-entry-summaries/download-jobs/{job_id}/file"),
            ("POST", "/api/tracker-entry-summaries/download/warm"),
            ("GET", "/api/tracker-template"),
            ("POST", "/api/tracker-template"),
            ("DELETE", "/api/tracker-template"),
            ("GET", "/api/tracker-entries"),
            ("GET", "/api/tracker-entries/missing-report"),
            ("GET", "/api/tracker-entries/missing-report/download"),
            ("PATCH", "/api/tracker-entries/{entry_id}"),
            ("GET", "/api/tracker-entries/{entry_id}"),
            ("GET", "/api/tracker-entries/{entry_id}/notice-file-view"),
            ("POST", "/api/tracker-entries/{entry_id}/notice-file-open-external"),
            ("POST", "/api/tracker-entries/{entry_id}/notice-file-warm"),
            ("GET", "/api/tracker-entries/{entry_id}/audit-logs"),
            ("GET", "/api/tracker-change-events/unread-count"),
            ("GET", "/api/tracker-change-events"),
            ("POST", "/api/tracker-change-events/mark-read"),
        }

        tracker_routes = {
            (next(iter(route.methods - {"HEAD", "OPTIONS"})), route.path)
            for route in tracker.router.routes
        }

        self.assertEqual(tracker_routes, expected_routes)
        for method, path in expected_routes:
            self._assert_route_is_owned_by_module(app.routes, method, path, "backend.api.routers.tracker")

    def test_runs_router_owns_run_paths(self) -> None:
        from backend.api.app import app
        from backend.api.routers import runs

        expected_routes = {
            ("POST", "/api/runs"),
            ("GET", "/api/runs"),
            ("GET", "/api/runs/{run_id}"),
            ("GET", "/api/runs/{run_id}/artifacts"),
            ("POST", "/api/runs/{run_id}/cancel"),
            ("GET", "/api/runs/{run_id}/logs"),
            ("GET", "/api/runs/{run_id}/events"),
            ("GET", "/api/run-presets"),
            ("POST", "/api/run-presets"),
        }

        runs_routes = {
            (next(iter(route.methods - {"HEAD", "OPTIONS"})), route.path)
            for route in runs.router.routes
        }

        self.assertEqual(runs_routes, expected_routes)
        for method, path in expected_routes:
            self._assert_route_is_owned_by_module(app.routes, method, path, "backend.api.routers.runs")

    def test_reports_router_owns_report_paths(self) -> None:
        from backend.api.app import app
        from backend.api.routers import reports

        expected_routes = {
            ("GET", "/api/reports/{report_name}"),
            ("POST", "/api/report-jobs"),
            ("GET", "/api/report-jobs"),
            ("GET", "/api/report-jobs/{job_id}"),
        }

        reports_routes = {
            (next(iter(route.methods - {"HEAD", "OPTIONS"})), route.path)
            for route in reports.router.routes
        }

        self.assertEqual(reports_routes, expected_routes)
        for method, path in expected_routes:
            self._assert_route_is_owned_by_module(app.routes, method, path, "backend.api.routers.reports")
