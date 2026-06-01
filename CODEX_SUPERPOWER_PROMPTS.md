# Codex Superpower Prompts

Use these prompt templates to get a Superpowers-like workflow in Codex.

## 1) Ask mode: investigate first
```text
Task:
[describe the problem]

Requirements:
- Follow AGENTS.md.
- Investigate first.
- Do not patch yet.
- Identify the likely failure stage or smallest safe plan.
- Be concise.
- Mention major regression risks.

Deliver:
1. task understanding
2. risk surface
3. likely failure stage or design pressure
4. smallest safe plan
5. targeted validation
```

## 2) Code mode: minimal patch
```text
Task:
[describe the implementation to make]

Requirements:
- Follow AGENTS.md.
- Implement the smallest safe patch.
- Avoid unrelated refactors.
- Preserve stable behavior unless the requested change requires it.
- End with targeted validation.

Deliver:
1. patch summary
2. files touched
3. major regression risks
4. targeted validation
```

## 3) Review mode: concise final check
```text
Task:
Review this diff for real issues only.

Requirements:
- Follow AGENTS.md.
- Ignore style nits unless they affect correctness.
- Focus on regressions, broken assumptions, false positive risk, unsafe overwrite behavior, and performance/fan-out risk if relevant.
- Report at most 3 major findings.

Deliver:
- Finding 1: ...
- Finding 2: ...
- Finding 3: ...

If none:
No major issues found in diff.
```

## 4) Candidate comparison
```text
Task:
Propose 2 to 3 small safe approaches for this issue.

Requirements:
- Follow AGENTS.md.
- Compare implementation size, regression risk, and expected precision/recall impact if search behavior is involved.
- Recommend the safest option.
```

## Recommended workflow
1. Run Ask mode first for non-trivial work.
2. Then run Code mode with the chosen plan.
3. Then run Review mode before you conclude.
4. Use Candidate comparison if the solution is unclear.
