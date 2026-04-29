# N10 — FalsePositiveVerifier (FPV)

**Type:** verifier
**Mode:** inline
**Active in:** `audit`

## Inputs

```
raw_findings: Finding[]   // fan-in from N04..N09 via E05
```

## Outputs

```
verified_findings: Finding[]          // passed the 4-question check
unverified_hypotheses: Finding[]      // demoted
location_verification_cache: {        // shared with N14 Pass A
  [canonical_file_path + ":" + line_range]: {
    verified: boolean,
    content_hash: string,             // sha256 of bytes read
    populated_by: "N10",
    populated_at: string              // ISO 8601
  }
}
```

## Side Effects

Read-only. Reads source files via Read tool to verify `file:line` locations. Populates `location_verification_cache` (in-memory only, not persisted).

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

## BACKTRACKING (single re-emit cap)

If a finding fails verification because the location seems wrong (possible hallucination in the analyzer), N10 may re-emit one request to the originating analyzer (N04..N09) via E06 with the correction context. The originating analyzer may revise the finding. The cap is one re-emit per finding — a revised finding that still fails is discarded.

## Location Verification Cache Contract

- N10 is the **only writer**. Writes after a successful Read.
- Key: `(canonical_path, line_range)` normalized as `(start_line, end_line)`.
- Failed Reads recorded as `verified: false` (no re-attempt by downstream consumers).
- Cache lives for one skill invocation; never persisted to disk.
- N14 Pass A consumes the cache (read-only); falls back to its own Read on cache miss.

## Token Budget

Scales with finding count. Budget per finding: ~500 tokens. Parallel fan-out across findings allowed (reads are independent).

## Backtrack / Aggregation

BACKTRACKING owner (audit side): initiates single re-emit to N04..N09 via E06.

## Fan-out Cardinality

1:many (per finding). Reads are parallelizable.

## Back-edge Endpoints

E06: N10 → N04..N09 (backtrack; single re-emit cap per finding).
