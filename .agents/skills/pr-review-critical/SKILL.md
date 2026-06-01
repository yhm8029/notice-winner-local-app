---
name: pr-review-critical
description: Use this skill when reviewing a diff, patch, or pull request and you want concise feedback limited to real critical issues, regressions, broken assumptions, or overfitting risk.
---

# PR Review Critical

## When to use
Use this skill when:
- reviewing a pull request
- reviewing a patch or diff
- checking whether a minimal fix introduces regressions
- validating that a change is production-safe

## Goal
Produce concise, high-signal review output.
Focus only on real critical issues.
Do not dilute review quality with style nits.

## Review rules
Review only for:
- real bugs
- regressions
- broken assumptions
- overfitting risk
- missed edge cases
- hidden behavior changes
- unsafe overwrite behavior
- latency/performance explosion if relevant

Do not comment on style unless it affects correctness.
Do not invent speculative issues without concrete reasoning.
Max 3 critical findings.

## Output format
Use this exact structure:
- 🔴 Critical 1: ...
- 🔴 Critical 2: ...
- 🔴 Critical 3: ...

If no critical issue exists, say:
`No critical issues found in diff.`

## Notes
- Prefer concrete reasoning over hypothetical concerns
- Stay within diff scope unless the diff clearly breaks a nearby contract
- Be concise
