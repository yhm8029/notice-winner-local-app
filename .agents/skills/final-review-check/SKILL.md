---
name: final-review-check
description: Use this skill when reviewing a patch, diff, or implementation result and you want concise high-signal feedback focused on real issues before finishing the task. Use proactively before declaring work complete.
---

# Final Review Check

## Goal
Produce concise, high-signal review output focused on real issues only.

## When to use
Use this skill when:
- a patch was just implemented
- a diff needs production-safety review
- the user wants regressions checked
- you are about to conclude a non-trivial coding task

## Rules
- Report at most 3 major findings
- Ignore style nits unless they affect correctness
- Focus on regressions, broken assumptions, overfitting risk, false linking risk, unsafe overwrite behavior, and latency/performance explosion if relevant
- Stay within diff scope unless a nearby contract is clearly broken
- If no major issue exists, say so plainly

## Output format
- Finding 1: ...
- Finding 2: ...
- Finding 3: ...

If none:
No major issues found in diff.
