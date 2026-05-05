# N15 — SaveHandler

**Type:** io
**Mode:** inline
**Active in:** `audit`
**Persistence:** conditional — writes to disk only under `--report` or `--reports`; otherwise emits inline summary and sets `saved_report_path=""`

## Inputs

```
validated_report: string                          // from N14 (frontmatter already populated)
tetrad_completeness: object                       // from N14
two_axis_scores: object                           // from N14
two_axis_scores_overridden_by_user: boolean       // from N14
falsifiability_survival_log: object               // from N10 via N14
detector_confidence_trace: object                 // from N00b via N14
section_selector_confidence: object               // from N02 via N14
project_model: (from N01)
resolved_flags: (from N01)
```

## Flag Gate

**If neither `--report` nor `--reports` is set:**
- Skip the save prompt entirely
- Do NOT write any files to disk
- Emit an inline summary of findings (severity distribution, top findings, two-axis scores) in conversation output
- Set `saved_report_path = ""`
- Set `save_decision = "inline-only"`
- Fire T3 tracer with `PATH=""` and `DECISION="inline-only"`
- Return — routing proceeds as normal (fix-offer, improve, or done)

**If `--report` or `--reports` is set:**
- Proceed with the save prompt and disk-write flow below

## Outputs

The audit-report-v1 schema places self-audit fields at TOP LEVEL in the YAML frontmatter (not nested). N15 enumerates each as a discrete output (no `self_audit_traces` wrapper):

```
save_decision: "accepted" | "declined"
saved_report_path: string | null    // null on decline
report_id: string                   // uuid v4
project_content_sha256: string      // computed at save time per §project_content_sha256

# --- Top-level frontmatter fields populated by N15 (matches audit-report-v1 schema) ---
detector_confidence: object                 // passed through from input
section_selector_confidence: object         // passed through from input
tetrad_completeness: object                 // passed through from input
two_axis_scores: object                     // passed through from input
two_axis_scores_overridden_by_user: boolean // passed through from input
falsifiability_survival_log: object         // passed through from input
```

**Structure rule (v2.0.1):** all six self-audit fields are written at the TOP LEVEL of the saved report's YAML frontmatter — never nested inside a `self_audit_traces` wrapper. The audit-report-v1 schema rejects the wrapper form (`additionalProperties: false` after v2.0.1 schema tightening).

## Side Effects

- Write-report: saves audit report to `~/docs/epiphany/audit/<project-slug>-<YYYYMMDD>-<HHMMSS>.md` on accept
- Write-state-file: writes `~/docs/epiphany/audit/.state/<report-id>.json` on accept only
- Write-log: structured event for save decision
- **TRACE (mandatory, non-blocking) — immediately after the save decision is made (whether accepted or declined), call this Bash command.** Substitute: `PATH` = full absolute path of the saved report (empty string if declined); `ID` = report_id uuid; `DECISION` = `accepted` or `declined`:
  ```
  python3 ~/.claude/skills/epiphany-audit-v2/scripts/langfuse_tracer.py audit-save --output-path "PATH" --report-id "ID" --save-decision "DECISION" 2>/dev/null || true
  ```

## Halt Conditions

None.

## Save Prompt

Offers save under `~/docs/epiphany/audit/`. Save prompt explicitly warns about idempotency degradation if user declines:

> "Declining to save means future `--fix` runs of this report cannot use state-file idempotency; they fall back to git-log only. Save anyway? (y/n)"

Writes idempotency state file at `~/docs/epiphany/audit/.state/<report-id>.json` only on save-accept.

## Idempotency State File

Written at save time. Format:
```json
{
  "report_id": "<uuid>",
  "audit_target": "<abs path>",
  "findings": {}
}
```
Populated with finding outcomes as `--fix` runs proceed. State file is authoritative over git-log during idempotency checks in N16.

## Project-Slug Derivation Per Input Type (v2.x)

| Input Type | Slug Derivation | Example |
|-----------|-----------------|---------|
| Code | `basename(audit_target)` (v1.x unchanged) | `CogVST-20260429-143000.md` |
| Specification document | `basename(file, '.md')-spec` | `enhanced-vst-playbook-spec-20260429-143000.md` |
| Plan document | `basename(file, '.md')-plan` | `migration-plan-20260429-143000.md` |
| Claude code ai agent skill | `basename(skill_dir)-skill` | `epiphany-audit-skill-20260429-143000.md` |
| Detailed prompt | `basename(file, '.md')-prompt` (strip date prefixes when redundant) | `prompt-graph-design-audit-orchestration-prompt-20260429-143000.md` |

All slugs are lowercased, non-alphanumeric chars → `-`, runs of `-` collapsed, leading/trailing `-` stripped, truncated to 80 chars.

## project_content_sha256 Computation and Storage (v2.x)

Computed at save time. Hashing scope per input type:

| Input Type | Hashing Scope |
|-----------|---------------|
| Code | `git ls-tree -r HEAD \| sha256sum` (if git repo); else `find . -type f -not -path './.git/*' -exec sha256sum {} \; \| sort \| sha256sum` |
| Spec/Plan/Prompt (single-file) | `sha256sum <file>` |
| Skill (directory) | `find <skill-dir> -type f -exec sha256sum {} \; \| sort \| sha256sum` |

Stored in audit report frontmatter as `project_content_sha256`. Used by N16 FixTriage for recency/staleness detection at `--fix` invocation.

## Self-Audit Trace Emission (v2.0.1)

Every report save renders the following six top-level fields directly in YAML frontmatter (NOT in an appended section, NOT nested in a wrapper):

- **detector_confidence** — from N00b: was input-type classification confident? on what fingerprints?
- **section_selector_confidence** — from N02: which sections activated/suppressed, why?
- **tetrad_completeness** — N14 Pass A check #2 result: every finding has all 4 tetrad tags
- **two_axis_scores** — N14 Pass A check #8 result: creativity score + functional_correctness score (the hard gate already passed at N14, but the scores are emitted for traceability)
- **falsifiability_survival_log** — N10 aggregated count of survived/downgraded/dropped findings (severity ≥ MEDIUM)
- **two_axis_scores_overridden_by_user** — true only if user waived the gate at N14

The full set is rendered by the audit-report.md.template at frontmatter top level. N15's only structural responsibility is to ensure the validated_report markdown's frontmatter contains all six fields before writing to disk; if N14's structural fix-up missed any, N15 inserts them as a final pre-save pass.

## Token Budget

Minimal (file write + prompt).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1 → user (save prompt, E12); then 1:1 → N24 (E16, `--improve` only) or → user (E21 fix-offer, no-flag mode).

## Back-edge Endpoints

None.
