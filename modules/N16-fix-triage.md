# N16 — FixTriage (F-VAL ingest + Resume-handler + Triage)

**Type:** validator
**Mode:** inline
**Active in:** `fix`

## Inputs

```
audit_report_path: string           // resolved per §1.3 <report> resolution order
resolved_flags: (from N01 or --fix entry)
recovery_manifest: object | null    // present when entered via resume
input_type: string                  // from report frontmatter (v2.x)
project_model: (from N01)           // for prerequisite check (v2.x)
```

## Outputs

```
triage_result: {
  source_report_id: string,
  source_audit_report_sha256: string,
  findings: TriagedFinding[]
}
fix_groups: FixGroup[]             // file/module-grouped, topo-sorted
topo_sorted_order: string[]        // finding-ids in execution order
```

## Side Effects

- Read: audit report file; state file at `~/docs/epiphany/audit/.state/<report-id>.json`
- Write-log: structured events per validation step and triage decision

## Halt Conditions

- `halt-pre-fix-on-validator-failure`: schema validation fail OR suspicious content user-declined
- `halt-on-empty-or-unfixable-report`: zero main-body findings (checked BEFORE suspicious-content and triage)
- `halt-on-conflicting-fixes` (live mode): two findings have incompatible edits (same line range)
- `halt-on-files-outside-tree`: report references files outside `audit_target` git tree
- `halt-on-invalid-finding-id`: `--escalate-finding F00N` references ID absent from report; checked after F-VAL passes but before triage; diagnostic lists available IDs
- `halt-on-resume-tree-divergence`: resume cleanup would discard working-tree changes outside prior run's scope
- `halt-on-stale-source-report`: report file missing or SHA-256 mismatch on resumed run
- `halt-on-mismatched-version`: `tool_version` skew; user declined
- `halt-on-user-abort`: ctrl-C at any interactive prompt

## Resume-Handler Sub-step (FIRST sub-step on resume entry)

Runs before F-VAL when entered via `resume` from `halt-on-recovery-conflict`. Order:
1. Run `git status --porcelain` + `git diff --name-only HEAD`
2. Tree-divergence safety check: if divergence includes files outside the in-flight finding's `location` AND outside the audit's flagged-files set → `halt-on-resume-tree-divergence` with options (a) discard and resume, (b) abort
3. On (a) or on clean divergence: run `git checkout -- . && git clean -fd`
4. Move `in_flight_finding_id` back to `pending` in recovery manifest
5. Proceed to normal F-VAL ingest

## Audit-Report Prerequisite Check (v2.x — mandatory at `--fix` and `--improve` invocation)

Runs BEFORE F-VAL ingest. Determines whether the audit report is recent enough to act on.

### Resolution Flow

1. **No `<report>` argument (v2.x canonical path):**
   - Resolve the target project via implied-context resolution
   - Derive the project slug per input-type slug rules
   - Search `~/docs/epiphany/audit/` for reports matching the slug pattern, ordered by timestamp descending
   - Zero reports → prompt: "No audit report found for this project. Run the audit first? (y/n)" → on `y`: route to audit pipeline then resume fix; on `n`: `halt-on-no-audit-report`
   - Exactly one report → use it
   - Multiple reports → list candidates with timestamps, ask user to select; ctrl-C → `halt-on-user-abort`

2. **Explicit `<report>` argument (v1.x back-compat path):**
   - Resolve per absolute path, cwd-relative, bare filename in `~/docs/epiphany/audit/`, then `fix-reports/`
   - Multiple matches → `halt-on-ambiguous-fix-report`
   - No match → `halt-on-unresolvable-fix-report`

### Recency / Staleness Detection

Once a report is resolved:

1. Compute current `project_content_sha256` per the hashing scope for the `input_type` (see N15 §project_content_sha256)
2. **Recent:** `current_sha256 == report.project_content_sha256` → proceed to F-VAL ingest
3. **Stale:** `current_sha256 != report.project_content_sha256` → prompt: "Audit report is stale (project modified since last audit). Re-run audit before applying fixes? (y/n)" → on `y`: re-audit then resume fix pipeline; on `n`: proceed with stale report under user acknowledgment; staleness recorded in run log
4. **Report file missing:** SHA-256 captured in metadata but file deleted → `halt-on-stale-source-report`
5. **No report found at all** (no-arg path) → prompt user to audit first (see resolution flow above)

### New Halt Conditions (v2.x)

- `halt-on-no-audit-report`: no report exists and user declined audit-first prompt
- `halt-on-stale-source-report`: report file missing (was referenced but deleted)

## F-VAL Ingest (schema validation)

- Parse YAML frontmatter + finding bodies from the audit report
- Validate parsed JSON against `schemas/audit-report-v1.schema.json`
- Capture SHA-256 of the report file as `source_audit_report_sha256`
- Extract `input_type` from report frontmatter for per-type routing downstream (v2.x)
- Suspicious-content prompt overrides `--auto` (requires explicit user confirmation)

## Idempotency Check

- State file authoritative; git-log fallback
- `reachable: false` annotations skipped unless `--reverify-state` was passed
- Conflict (state says applied at SHA not in current branch) → warn + user choice: (a) re-apply, (b) skip, (c) abort

## Triage Rules

1. Group findings by file/module
2. Topo-sort within each group (dependency: finding A depends on B iff A's location is at or after B's remediation diff lines)
3. Tier classification per §2.3 rules (Tier-1/2/3 + defer-on-uncertainty)
4. Conflicting-edit detection: in live mode → `halt-on-conflicting-fixes`; under `--dry-run` → record in `triage_summary.conflicting_groups` and continue

## Conflicting Edits Definition

Two findings have **incompatible** edits iff their remediation diffs both modify any character within the same line range, OR both insert content at the same line. Non-overlapping edits within the same file (different line ranges) are **compatible** and merged into one fix-group. Three-or-more-way: any pair failing compatibility halts the cluster.

## Token Budget

Moderate. Prerequisite check reads report frontmatter and computes `project_content_sha256` (O(files) for skill/code types; O(1) for single-file types). F-VAL reads audit report and state file; triage logic scales with finding count.

## Backtrack / Aggregation

AGGREGATION owner (fix side: file-grouping). CONDITIONAL ROUTING owner.

## Fan-out Cardinality

N:1 (aggregates findings into fix-groups).

## Back-edge Endpoints

E_rerun_fail: N21 → N16 (re-triage with regression context).
