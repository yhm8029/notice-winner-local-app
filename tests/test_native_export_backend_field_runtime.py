from __future__ import annotations

from dataclasses import dataclass
import unittest

from backend.services.native_export_backend_field_runtime import build_resolved_export_fields


@dataclass(frozen=True)
class ExtractedFields:
    winner_name: str = ""
    winner_pattern: str = ""
    gross_area_scale: str = ""
    construction_cost: str = ""
    demand_contact: str = ""
    client_location: str = ""
    site_location: str = ""
    construction_start_date: str = ""
    construction_duration_days: str = ""
    completion_expected_date_explicit: str = ""
    building_automation_estimated_amount: str = ""
    demand_contact_resolution_status: str = ""


@dataclass(frozen=True)
class ResolvedField:
    value: str = ""
    source: str = ""


class NativeExportBackendFieldRuntimeTests(unittest.TestCase):
    def test_build_resolved_export_fields_assembles_fallbacks_and_flags(self) -> None:
        contract_hit = type(
            "ContractHit",
            (),
            {
                "contract_name": "contract winner",
                "contract_amount": "2000",
                "site_name": "busan",
                "contract_duration_days": "45",
                "contract_date": "2026-04-01",
            },
        )()
        extracted = ExtractedFields(
            winner_name="notice winner",
            winner_pattern="notice_pattern",
            gross_area_scale="300",
            construction_cost="1000",
            client_location="seoul",
            construction_start_date="2026-05-01",
        )

        resolved = build_resolved_export_fields(
            extracted=extracted,
            contract_hit=contract_hit,
            best_row={"g2b_verified": "Y"},
            manual_overrides={},
            external_portal_contact_expected_blank=True,
            presmpt_prce="1500",
            org_name="demo org",
            resolved_field_cls=ResolvedField,
            format_won_fn=lambda value: f"won:{value}" if str(value or "").strip() else "",
            normalize_export_contact_value_fn=lambda value, _org_name: value.strip(),
            resolve_field_fn=lambda confirmed_value, fallback_value="", fallback_source="": (
                ResolvedField(str(confirmed_value).strip(), "confirmed_extracted")
                if str(confirmed_value or "").strip()
                else ResolvedField(str(fallback_value).strip(), fallback_source) if str(fallback_value or "").strip() else ResolvedField()
            ),
            looks_like_specific_architecture_firm_name_fn=lambda name: name == "contract winner",
            resolve_contract_source_type_fn=lambda _contract_hit, _winner_name: "g2b_contract_api",
            select_building_automation_cost_candidate_fn=lambda **_kwargs: ("won:2000", "contract_amount"),
            resolve_building_automation_amount_fn=lambda **_kwargs: ResolvedField("120", "estimated_contract_amount"),
            compute_completion_expected_date_fn=lambda **_kwargs: "2026-05-16",
            resolve_contract_status_fn=lambda **_kwargs: "FOUND",
            resolve_contract_score_fn=lambda _contract_hit, _winner_name: 0.87,
            resolve_contract_reason_code_fn=lambda **_kwargs: "MATCH",
            resolve_contract_winner_pattern_fn=lambda _contract_hit, _winner_name, extracted_pattern: f"resolved:{extracted_pattern}",
            resolve_contract_evidence_fn=lambda _contract_hit, _winner_name: "g2b_contract:demo",
            resolve_contract_hit_note_fn=lambda _contract_hit, _winner_name: "g2b_contract_hit",
            build_fallback_notes_fn=lambda fields: [f"contract_amount={fields['contract_amount'].source}"],
        )

        self.assertEqual(resolved.winner_name, "contract winner")
        self.assertEqual(resolved.contract_amount.value, "won:2000")
        self.assertEqual(resolved.site_location.value, "busan")
        self.assertEqual(resolved.architect_office.value, "contract winner")
        self.assertEqual(resolved.status, "FOUND")
        self.assertEqual(resolved.score, "0.87")
        self.assertTrue(resolved.expected_blank_external_portal)
        self.assertEqual(resolved.fallback_notes, ["contract_amount=confirmed_extracted"])


if __name__ == "__main__":
    unittest.main()
