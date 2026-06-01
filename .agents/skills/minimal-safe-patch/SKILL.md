---
name: minimal-safe-patch
description: Use this skill when implementing a change after planning is complete. Keep diffs minimal, avoid unrelated refactors, and preserve stable behavior unless the requested change requires it.
---

# Minimal Safe Patch

## Goal
Implement the smallest safe patch for the already-identified problem or plan.

## When to use
Use this skill when:
- the likely failure stage is already known
- the design choice is already made
- the task is implementation-focused
- you need a safe production patch rather than a broad cleanup

## Rules
- Keep the diff minimal
- Avoid unrelated refactors
- Preserve stable tracker-facing behavior unless the user requested a behavior change
- Do not silently widen search or overwrite behavior
- If search behavior changes, mention precision/recall impact
- If data update behavior changes, mention overwrite or backfill safety
- End with targeted validation

## Output format
[Patch summary]
...

[Files touched]
...

[Critical regression risks]
- ...

[Targeted validation]
...
