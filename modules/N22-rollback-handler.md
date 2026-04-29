# N22 — RollbackHandler

**Type:** recovery
**Mode:** inline
**Active in:** `fix`

## Inputs

```
trigger: "e_repair_cap_hit" | "e_finalize"
fix_report_id: string | null     // populated on e_finalize (after N23 writes fix report)
recovery_manifest_path: string
failed_fix_group: FixGroup | null  // present on cap-hit trigger
```

## Outputs

```
recovery_manifest_finalized: object
archive_path: string | null   // populated on e_finalize (completed archive)
```

## Side Effects

- Write-recovery-manifest: finalize recovery manifest (boundary-aligned boundary write)
- On E_finalize: archive manifest to `.recovery/.archive/<report-id>-completed-<ISO-timestamp>.json` and REMOVE live `<report-id>.json`
- Write-log

## Halt Conditions

None. N22 emits a diagnostic if cap-hit blocks all remaining work, but does not halt itself.

## Responsibilities

N22 has exactly three responsibilities — nothing more:

**(a) E_repair cap-hit for a fix-group:**
Finalize recovery manifest with failure record for the failed fix-group. Manifest STAYS LIVE at `~/docs/epiphany/audit/.recovery/<report-id>.json` so the user can `resume` next run.

**(b) E_finalize (planned termination):**
1. N23 has already written the fix report file to disk and generated `fix_report_id`
2. E_finalize fires → N22 reads the just-written fix report to extract `fix_report_id`
3. N22 writes final manifest record including `fix_report_id`
4. N22 archives manifest: moves to `.recovery/.archive/<report-id>-completed-<ISO-timestamp>.json`
5. N22 removes live `<report-id>.json` so subsequent `--fix` runs do NOT trip `halt-on-recovery-conflict`
6. E_complete fires → user summary

**(c) Mid-flight death (process kill, OS crash):**
N22 cannot act. The at-rest state is the most recent fix-group boundary write from N19 (which is sufficient for the resume-handler to restart the in-flight fix-group). N22 cannot address this case — it is handled entirely by N19's write discipline and N16's resume-handler.

## NEVER `git revert HEAD`

Failed fix attempts never reach `git commit` (the atomic loop in N19 discards working-tree changes before committing). N22 has nothing to revert. `git revert` would create spurious commits that break idempotency grep.

## Sequencing with E_finalize (strictly sequential)

1. N23 generates `fix_report_id` and writes fix report to disk
2. E_finalize fires (carrying `fix_report_id`)
3. N22 reads fix report, writes manifest, archives manifest
4. E_complete fires → user

This order is non-negotiable. N22 must NOT archive the manifest before N23 writes the report.

## Token Budget

Minimal (file operations).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1.

## Back-edge Endpoints

E_complete: N22 → user (terminal).
