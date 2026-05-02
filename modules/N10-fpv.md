# N10 — FalsePositiveVerifier (FPV)

**Type:** verifier
**Mode:** inline
**Active in:** `audit`

## Inputs

```
raw_findings: Finding[]   // fan-in from N04..N09 via E05
project_model: object     // for falsifiability counter-argument context
resolved_flags: object    // for --deep gating of expanded counter-argument generation
```

## Outputs

```
verified_findings: Finding[]          // passed the 4-question check; carry falsifiability block on severity ≥ MEDIUM
unverified_hypotheses: Finding[]      // demoted
location_verification_cache: {        // shared with N14 Pass A
  [canonical_file_path + ":" + line_range]: {
    verified: boolean,
    content_hash: string,             // sha256 of bytes read
    populated_by: "N10",
    populated_at: string              // ISO 8601
  }
}
falsifiability_survival_log: {        // aggregated across all severity ≥ MEDIUM findings
  survived: integer,
  downgraded: integer,
  dropped: integer
}
```

## Side Effects

Read-only. Reads source files via Read tool to verify `file:line` locations AND to construct falsifiability counter-arguments with full context. Populates `location_verification_cache` (in-memory only, not persisted).

## Halt Conditions

None.

## Four False-Positive Questions (applied to each finding)

1. `intentional`: Is this behavior intentional by design?
2. `file_symbol_verified`: Does the symbol/function/line actually exist at the cited location?
3. `reachable_from_entry`: Is this code reachable from a declared entry point?
4. `fix_breaks_dependents`: Would applying the proposed fix break callers?

## Disposition Rules (deterministic)

| Condition | Disposition |
|-----------|-------------|
| `file_symbol_verified.value == false` | **Discard** entirely (not even Unverified Hypothesis) |
| `intentional.value == true` | **Demote** to Unverified Hypotheses; notes: "demoted: code appears intentional ({{justification}})" |
| `reachable_from_entry.value == false` AND severity ∈ {CRITICAL, HIGH} | **Demote** to Unverified Hypotheses; notes: "demoted: unreachable from entry but claimed {{severity}}" |
| `reachable_from_entry.value == false` AND severity ∈ {MEDIUM, LOW, INFO} | **Pass** with notes: "unreachable from declared entry points" |
| `fix_breaks_dependents.value == true` AND `confidence == HIGH` | **Pass**; remediation MUST address dependents |
| `fix_breaks_dependents.value == true` AND `confidence < HIGH` | **Demote** to Unverified Hypotheses; notes: "demoted: fix would break dependents; confidence below HIGH floor" |
| All four pass | **Pass** unconditionally |

## Falsifiability-First Check (v2.x — moved from N13 in v2.0.1)

For every finding with **severity ≥ MEDIUM** that survives the 4-question disposition above:

1. Generate the strongest available counter-argument against the finding. Use:
   - The finding's `evidence_excerpt` and `rationale`
   - A targeted Read of up to 2-3 lines of context BEFORE and AFTER `location` (using `location_verification_cache` if already populated for this location; otherwise issuing a fresh Read)
   - Under `--deep`: also Read up to one neighboring file referenced in the rationale (sibling module, called function, etc.)
2. Evaluate whether the finding's evidence withstands the counter-argument.
3. Disposition:
   - **survived** → emit finding with `falsifiability.status: "survived"`, `falsifiability.counter_argument: <text>`, `falsifiability.survival_rationale: <text>`. Increment `falsifiability_survival_log.survived`.
   - **downgraded** → lower severity by one tier (CRITICAL → HIGH → MEDIUM). Emit with `falsifiability.status: "downgraded"`. Increment `falsifiability_survival_log.downgraded`.
   - **dropped** → counter-argument is decisive; remove finding from output entirely. Increment `falsifiability_survival_log.dropped`.

LOW and INFO severity findings skip the falsifiability check (cost-vs-value); they pass through with no `falsifiability` block.

This relocation (v2.0.1) places the check at the layer that already has source-file Read access and the location cache, eliminating the v2.0.0 bug where N13 was nominally responsible for falsifiability but lacked file access. N13 now only renders the existing `falsifiability` block in markdown.

## BACKTRACKING (single re-emit cap)

If a finding fails verification because the location seems wrong (possible hallucination in the analyzer), N10 may re-emit one request to the originating analyzer (N04..N09) via E06 with the correction context. The originating analyzer may revise the finding. The cap is one re-emit per finding — a revised finding that still fails is discarded.

## Location Verification Cache Contract

- N10 is the **only writer**. Writes after a successful Read.
- Key: `(canonical_path, line_range)` normalized as `(start_line, end_line)`.
- Failed Reads recorded as `verified: false` (no re-attempt by downstream consumers).
- Cache lives for one skill invocation; never persisted to disk.
- N14 Pass A consumes the cache (read-only); falls back to its own Read on cache miss.

## Token Budget

Scales with finding count. Budget per finding: ~2,000-4,000 tokens for the FP check (evidence gathering 2-3k + disposition logic ~500). Falsifiability adds ~1,500-2,500 tokens per severity ≥ MEDIUM finding (counter-argument generation + survival evaluation). Parallel fan-out across findings allowed (reads are independent).

## Backtrack / Aggregation

BACKTRACKING owner (audit side): initiates single re-emit to N04..N09 via E06. AGGREGATION owner of `falsifiability_survival_log`.

## Fan-out Cardinality

(v2.0.2) — three outgoing edges:
- E07: 1:1 → N11 (verified findings)
- E_log_thread: 1:1 → N14 (falsifiability_survival_log; direct edge, bypasses N11/N12/N13 which do not carry the log payload)
- E06: 1:N → N04..N09 (backtrack, single re-emit cap per finding)

Internal parallelism across findings is allowed (reads are independent).

## Back-edge Endpoints

E06: N10 → N04..N09 (backtrack; single re-emit cap per finding).
