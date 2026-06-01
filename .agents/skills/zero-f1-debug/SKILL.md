---
name: zero-f1-debug
description: Use this skill when a golden-set case, expected related notice, or project match is missed entirely and you need to locate the exact failure stage before proposing a fix.
---

# Zero-F1 Debug

## When to use
Use this skill when:
- a golden-set item is missed
- an expected related notice is not retrieved
- recall is effectively zero for a target case
- a project match disappears after a recent search/ranking change
- you need to isolate the exact failure stage before editing code

## Goal
Find the exact failure stage for a missed match.
Propose the smallest high-confidence fix.
Do not broaden retrieval blindly.

## Required analysis order
Always follow this order:

1. Confirm expected positive target
2. Check normalization mismatch
3. Check tokenization mismatch
4. Check query generation miss
5. Check retrieval miss
6. Check ranking/filter rejection
7. Check dedup/post-processing exclusion
8. Identify exact failure point

Do not propose a fix before locating the failure stage.

## Fix policy
- Prefer surgical fixes over broad recall expansion
- Explicitly discuss precision risk of any fix
- If the proposed fix is heuristic, say so
- If the problem may be label ambiguity or data ambiguity, say so
- Avoid one-case overfitting
- Avoid changing multiple retrieval layers at once unless necessary

## Review focus
Review only for:
- incorrect failure-stage diagnosis
- overfitting risk
- broadening retrieval without guardrails
- hidden precision regressions
- missed downstream exclusion logic

## Validation checklist
Validate against:
1. the target missed case
2. one similar near-match case that should stay excluded
3. one normalization-variant case
4. one issuer-sensitive case if relevant
5. one dedup/post-processing case if relevant

If golden-set or zero-F1 tooling exists, prefer it over ad hoc examples.

## Output format
Use this structure:

[Expected match]
...

[Failure stage]
...

[Root cause]
...

[Candidate fix]
...

[Precision risk]
...

[Validation against similar cases]
...
