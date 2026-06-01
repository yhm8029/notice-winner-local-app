from __future__ import annotations

from unittest import TestCase

from backend.services.tracker_contact_source_diagnostics import summarize_tracker_contact_sources


class TrackerContactSourceDiagnosticsTests(TestCase):
    def test_summarize_tracker_contact_sources_groups_counts_and_unique_samples(self) -> None:
        payload = summarize_tracker_contact_sources(
            [
                {
                    "project_name": "Project A",
                    "demand_contact": "문화기반조성과/062-613-3482",
                    "demand_contact_source": "confirmed_extracted",
                },
                {
                    "project_name": "Project B",
                    "demand_contact": "조성일/053-233-0162",
                    "demand_contact_source": "fallback_seed_contact",
                },
                {
                    "project_name": "Project C",
                    "demand_contact": "조성일/053-233-0162",
                    "demand_contact_source": "fallback_seed_contact",
                },
                {
                    "project_name": "Project D",
                    "demand_contact": "",
                    "demand_contact_source": "",
                },
            ]
        )

        self.assertEqual(
            payload["source_counts"],
            [
                {"source": "fallback_seed_contact", "count": 2},
                {"source": "confirmed_extracted", "count": 1},
                {"source": "missing", "count": 1},
            ],
        )
        self.assertEqual(
            payload["source_samples"][0],
            {
                "source": "fallback_seed_contact",
                "samples": [{"project_name": "Project B", "demand_contact": "조성일/053-233-0162"}],
            },
        )
        self.assertEqual(payload["source_samples"][2], {"source": "missing", "samples": []})
