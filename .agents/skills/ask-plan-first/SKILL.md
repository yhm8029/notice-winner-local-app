---
name: ask-plan-first
description: Use this skill for any non-trivial task when you should investigate and plan first before making code changes. Prefer this skill proactively unless the change is a very small obvious patch.
---

# Ask Plan First

## Goal
Understand the task, identify the risk surface, and produce the smallest safe implementation plan before editing code.

## When to use
Use this skill when:
- the task touches multiple modules
- the correct failure stage is unclear
- the patch could affect search, ranking, dedup, extraction, or tracker behavior
- regression risk matters
- the user asks for investigation, diagnosis, design, or a safe plan first

## Rules
- Do not patch yet
- Be concise
- Identify likely failure stage or risk surface first
- Prefer the smallest safe implementation
- Explicitly mention precision/recall tradeoff if search behavior may change
- Explicitly mention overwrite or data churn risk if field update behavior may change

## Output format
[Task understanding]
...

[Risk surface]
...

[Likely failure stage or design pressure]
...

[Smallest safe plan]
...

[Targeted validation]
...
