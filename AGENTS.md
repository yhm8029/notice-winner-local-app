# AGENTS.md

## Project overview
This repository is an operational pipeline and web app for collecting, linking, extracting, storing, and tracking notice/project information over time.

This is **not** a one-off summarizer.
Changes must preserve production behavior, data stability, and operator trust.

Current branch focus:
- related notice search
- project-level linking of related notices
- safe expansion of retrieval/search behavior
- preserving tracker stability while improving recall

---

## Core principles
1. Regression safety over elegance
2. Minimal diffs over broad refactors
3. Explicit business rules over hidden heuristics
4. Stable project-level behavior over aggressive retrieval expansion
5. Observable reasoning over opaque scoring changes
6. Conservative overwrite policy for extracted fields
7. Precision/recall tradeoff must be explicitly discussed when search behavior changes

---

## What Codex should do by default
For any non-trivial task, follow this workflow:

1. Understand the task
2. Identify touched modules and regression surface
3. Propose the smallest safe plan
4. Implement minimal patch
5. Review for critical regressions
6. Suggest targeted validation

Be concise.
Do not over-explain.
Do not do unrelated cleanup unless explicitly requested.

---

## Required output style
Use this structure unless the user asks otherwise:

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

If there are no critical issues, say:
`No critical issues found.`

---

## Branch-specific goals: related notice search
This branch improves retrieval/linking of related notices around a project.

When changing related notice search logic, always evaluate impact on:

- query generation breadth
- normalization behavior
- token coverage
- issuer/org matching
- ranking thresholds
- dedup behavior
- tracker stability
- latency / fan-out cost
- golden-set precision/recall changes
- false linking risk between similar projects

Do not silently broaden search behavior.
Do not silently tighten thresholds.
Always call out likely recall gains and precision risks.

---

## Safe change rules
### 1. Keep diffs minimal
- Prefer surgical patches
- Avoid broad structural rewrites unless explicitly requested
- Avoid renaming/moving files without strong reason

### 2. Preserve behavior unless explicitly changing it
- Existing stable behavior should remain stable
- If behavior changes intentionally, state it clearly

### 3. No hidden widening of retrieval
- Any query expansion, fallback broadening, token loosening, or threshold lowering must be explicitly justified
- Mention possible false positive risk

### 4. No hidden tightening of retrieval
- Any threshold increase, stricter filtering, or narrower query behavior must explicitly mention recall risk

### 5. Conservative overwrite policy
- Prefer blank -> filled
- Be cautious with nonblank -> nonblank replacement
- Do not introduce aggressive overwrite behavior unless explicitly requested

---

## Related notice search rules
When working on related notice search, prefer this analysis order:

1. Confirm intended project anchor
2. Check project name normalization
3. Check tokenization / token loss
4. Check query variant generation
5. Check retrieval coverage
6. Check ranking / scoring rejection
7. Check dedup / post-processing exclusion
8. Check final tracker/export inclusion

Do not jump to a broad heuristic before locating the actual failure stage.

Prefer:
- anchor-preserving fixes
- issuer-aware narrowing when broadening recall
- scoring/ranking explanations that are inspectable
- limited search expansion over open-ended fuzziness

Avoid:
- global looseness without guardrails
- implicit “more results is better” behavior
- changes that can cause unrelated notices to cluster together

---

## Precision / recall policy
This codebase is sensitive to both precision and recall.

Default rule:
- For exploratory search: recall can be improved carefully
- For final linking / tracker-facing behavior: precision guardrails matter more

Any patch that may affect golden-set metrics should explicitly mention:
- expected recall impact
- expected precision impact
- likely affected case types

Examples of risky case types:
- similar school/facility names
- project names with generic suffixes
- same issuer, different construction phase
- project names with truncated or transformed wording
- “extension / phase / district / zone / remodeling” variants

---

## Review policy
Review only for:
- real bugs
- regressions
- broken assumptions
- overfitting risk
- missed edge cases
- latency/fan-out explosions
- unstable ranking behavior
- unsafe overwrite behavior

Ignore style nits unless they affect correctness.

Max 3 critical findings.

---

## Validation policy
Prefer targeted validation over broad expensive testing.

When changing related notice search, prioritize:
1. one exact-match happy path
2. one normalization-variant case
3. one near-duplicate false positive guard case
4. one issuer-sensitive disambiguation case
5. one dedup/post-processing survival case
6. one latency/fan-out sanity check if search expansion changed

If golden-set or zero-F1 tooling exists, prefer using it over ad hoc examples.

---

## Files/modules likely to matter
This list is indicative, not exhaustive.

Potentially relevant areas:
- project search / related notice search
- search normalizer
- tokenizer
- query builder
- ranking / scoring
- dedup / linking logic
- tracker export / tracker entries
- backend services related to notice retrieval
- tests around search, ranking, or tracker behavior

Before changing code, identify the smallest module boundary that can solve the task.

---

## What to avoid
- broad refactors during bugfix work
- changing multiple scoring dimensions at once unless necessary
- silent threshold changes
- introducing opaque heuristics without rationale
- overwriting stable extracted values aggressively
- fixing recall by collapsing precision guardrails
- fixing one golden-set miss by overfitting to one title pattern

---

## If the task is ambiguous
Default to the more conservative implementation.
State assumptions explicitly.
Do not invent product requirements.

---

## Done criteria
A task is not done unless:
- the intended change is implemented
- regression risks were considered
- critical review was performed
- targeted validation was proposed
- precision/recall impact was mentioned if search behavior changed
