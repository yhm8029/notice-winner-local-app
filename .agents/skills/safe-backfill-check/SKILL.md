---
name: safe-backfill-check
description: Use this skill when evaluating whether an extraction or backfill change is safe for production, especially for blank-to-filled vs nonblank replacement policies and source reliability.
---

# Safe Backfill Check

## When to use
Use this skill when:
- changing extraction overwrite rules
- reviewing blank -> filled policies
- reviewing nonblank -> nonblank replacement safety
- evaluating whether a source is strong enough for backfill
- checking operational safety of extracted field updates

## Goal
Decide whether a backfill or overwrite policy is safe enough for production use.
Prefer conservative field update behavior.

## Required evaluation
Always evaluate:
1. source reliability
2. common false positive patterns
3. common false negative patterns
4. whether blank -> filled is safe
5. whether nonblank replacement is safe
6. whether the policy should be allow / restrict / block / fallback-only

## Policy rules
- Prefer conservative policies
- Avoid optimistic extraction from weak textual hints
- Separate strong sources from weak textual clues
- If source precision is poor, recommend restriction even at some recall cost
- Explicitly distinguish data fill from overwrite
- Avoid hidden data churn

## Output format
Use this structure:

[Field]
...

[Current policy]
...

[False positive risk]
...

[False negative risk]
...

[Recommended policy]
...

[Overwrite safety]
...

[Operational recommendation]
...
