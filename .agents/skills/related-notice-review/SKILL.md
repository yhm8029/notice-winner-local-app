---
name: related-notice-review
description: Use this skill when reviewing or implementing changes related to related notice search, project-level notice linking, query expansion, ranking, dedup, or recall/precision tradeoffs.
---

# Related Notice Review

## When to use
Use this skill when the task involves any of the following:
- related notice search behavior
- project-level linking of related notices
- normalization or tokenization affecting retrieval
- query variant generation
- ranking or threshold changes
- dedup or post-processing exclusions
- false positive linking between similar projects
- recall/precision regressions in related notice retrieval

## Goal
Improve related notice retrieval and linking safely.
Preserve tracker stability.
Avoid broad recall fixes that collapse precision guardrails.

## Required analysis order
Follow this order before proposing a fix:

1. Confirm intended project anchor
2. Check project name normalization
3. Check tokenization / token loss
4. Check query variant generation
5. Check retrieval coverage
6. Check ranking / scoring rejection
7. Check dedup / post-processing exclusion
8. Check final tracker/export inclusion

Do not jump directly to broad heuristics or threshold loosening.

## Implementation rules
- Prefer minimal, anchor-preserving fixes
- Prefer issuer-aware narrowing when broadening retrieval
- Explain expected recall gain and precision risk
- Do not change multiple scoring dimensions at once unless necessary
- Do not silently widen fallback behavior
- Do not silently tighten filters
- Avoid open-ended fuzziness
- Avoid heuristic growth without guardrails

## Review focus
Review only for:
- real bugs
- regressions
- false linking risk
- precision collapse risk
- recall collapse risk
- unstable ranking behavior
- latency/fan-out explosions
- dedup/post-processing mistakes

Ignore style-only comments.
Max 3 critical findings.

## Validation checklist
Prefer targeted validation over broad testing.
Check:
1. one exact-match happy path
2. one normalization-variant case
3. one near-duplicate false positive guard case
4. one issuer-sensitive disambiguation case
5. one dedup/post-processing survival case
6. one latency/fan-out sanity check if search expansion changed

If golden-set or zero-F1 tooling exists, prefer it.

## Output format
Use this structure:

[Task understanding]
...

[Failure / risk stage]
...

[Plan]
...

[Patch summary]
...

[Critical review]
- 🔴 Critical 1: ...
- 🔴 Critical 2: ...
- 🔴 Critical 3: ...

[Validation]
...

If no critical issue exists, say:
`No critical issues found.`
