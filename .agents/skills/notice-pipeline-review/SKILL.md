---
name: notice-pipeline-review
description: Use this skill when reviewing or implementing changes across the operational notice pipeline, especially where retrieval, extraction, linking, tracking, export, or regression safety all matter together.
---

# Notice Pipeline Review

## When to use
Use this skill when the task spans multiple parts of the notice pipeline, including:
- retrieval/search changes
- extraction logic changes
- linking or dedup behavior
- tracker/export behavior
- production-safe refactors
- regression-oriented implementation reviews

## Goal
Make safe, minimal, production-ready changes across the operational notice pipeline.
Prioritize regression safety and explicit business rules over elegance.

## Working principles
- This is an operational pipeline, not a toy script
- Regression risk matters more than elegance
- Favor deterministic behavior
- Favor observable reasoning in code paths
- Prefer safe backfill / safe replace policies over aggressive overwrite
- Avoid hidden behavior changes
- Keep business rules explicit

## Required workflow
1. Restate the task briefly
2. Identify touched modules
3. Identify regression surface
4. Propose the smallest valid plan
5. Implement minimal patch
6. Review for critical issues
7. Propose targeted validation

## Review focus
Review only for:
- real bugs
- regressions
- broken assumptions
- overfitting risk
- missed edge cases
- hidden behavior changes
- unstable ranking/dedup behavior
- unsafe overwrite behavior

Max 3 critical findings.
Ignore style nits unless they affect correctness.

## Output format
Use this structure:

[Task understanding]
...

[Risk surface]
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
