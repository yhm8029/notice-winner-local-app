from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContactObservation:
    candidate_text: str = ""
    contact: str = ""
    dept: str = ""
    phone: str = ""
    line: str = ""
    line_idx: int = 0
    score: int = 0
    is_anchor: bool = False
    evidence_block_text: str = ""
    evidence_block_type: str = "line_cluster"
    evidence_block_index: int = 0
    phase_hint: str = "notice"
    role_hint: str = "unknown"
    owner_side_hint: str = "unknown"
    owner_side_basis_hint: str = "unknown"


@dataclass(frozen=True)
class ContactResolution:
    contact: str = ""
    status: str = "no_owner_candidate"
    reason: str = ""
    phase: str = "unknown"
    role: str = "unknown"
    owner_side: str = "unknown"
    owner_side_basis: str = "unknown"
    observation: ContactObservation | None = None


def resolve_contact_from_observations(observations: list[ContactObservation]) -> ContactResolution:
    if not observations:
        return ContactResolution(status="no_owner_candidate", reason="no_observations")

    ranked = sorted(observations, key=_contact_resolution_sort_key, reverse=True)
    auto_pick_candidates = [row for row in ranked if _is_auto_pick_eligible(row)]
    if auto_pick_candidates:
        top = auto_pick_candidates[0]
        competing = [
            row
            for row in auto_pick_candidates[1:]
            if _contact_resolution_sort_key(row) == _contact_resolution_sort_key(top)
            and str(row.contact or "").strip() != str(top.contact or "").strip()
        ]
        comparable_competing = [
            row
            for row in competing
            if str(row.dept or "").strip() != str(top.dept or "").strip()
            or int(row.evidence_block_index or 0) != int(top.evidence_block_index or 0)
        ]
        if comparable_competing:
            return ContactResolution(
                status="review",
                reason="auto_pick_conflict",
                observation=top,
                phase=top.phase_hint,
                role=top.role_hint,
                owner_side=top.owner_side_hint,
                owner_side_basis=top.owner_side_basis_hint,
            )
        return ContactResolution(
            contact=str(top.contact or "").strip(),
            status="resolved",
            reason="auto_pick_owner_notice" if top.phase_hint == "notice" else "auto_pick_owner_guideline",
            observation=top,
            phase=top.phase_hint,
            role=top.role_hint,
            owner_side=top.owner_side_hint,
            owner_side_basis=top.owner_side_basis_hint,
        )

    owner_side_candidates = [
        row
        for row in ranked
        if row.role_hint == "owner_contact"
    ]
    if owner_side_candidates:
        top = owner_side_candidates[0]
        return ContactResolution(
            status="review",
            reason="owner_candidate_needs_review",
            observation=top,
            phase=top.phase_hint,
            role=top.role_hint,
            owner_side=top.owner_side_hint,
            owner_side_basis=top.owner_side_basis_hint,
        )

    return ContactResolution(status="no_owner_candidate", reason="no_owner_candidate")


def _contact_resolution_sort_key(row: ContactObservation) -> tuple[int, int, int, int, int]:
    phase_rank = 0
    if row.phase_hint == "notice":
        phase_rank = 3
    elif row.phase_hint == "competition_guideline":
        phase_rank = 2
    elif row.phase_hint == "result_announcement":
        phase_rank = 1
    owner_rank = {"yes": 2, "uncertain": 1, "no": 0}.get(str(row.owner_side_hint or ""), 0)
    basis_rank = {
        "explicit_owner_org_match": 4,
        "school_admin_office": 3,
        "owner_subordinate_org": 2,
        "inferred_only": 1,
        "unknown": 0,
    }.get(str(row.owner_side_basis_hint or ""), 0)
    return (
        1 if bool(row.is_anchor) else 0,
        owner_rank,
        phase_rank,
        basis_rank,
        int(row.score or 0),
    )


def _is_auto_pick_eligible(row: ContactObservation) -> bool:
    if row.role_hint != "owner_contact":
        return False
    if row.owner_side_hint != "yes":
        return False
    if row.phase_hint not in {"notice", "competition_guideline"}:
        return False
    return True
