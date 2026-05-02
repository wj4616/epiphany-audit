# N19 — FixApplier

**Type:** actuator
**Mode:** inline (write-serial; NEVER fan-out)
**Active in:** `fix`

## Inputs

```
fix_groups: FixGroup[]          // topo-sorted from N16
user_approvals: object          // from N17
baseline_metrics: object        // from N18
branch_name: string             // from N18
input_type: string              // from N16 triage (v2.x — drives transactional scope)
```

## Outputs

```
per_fix_outcomes: FixOutcome[]
recovery_manifest_updates: RecoveryEvent[]
```

## Side Effects

- Git-staged: working-tree edits + commits on PASS; `git checkout -- <tracked-touched-files>` + `git clean -fd <new-files-created-by-this-attempt>` on FAIL (NEVER `git revert`)
- Write-recovery-manifest: boundary-aligned writes ONLY at fix-group start, end-success, end-failure (see Atomic Loop section below and Recovery-Manifest Write Policy section)
- Write-log: events per fix-group iteration

## Halt Conditions

- `halt-mid-fix-on-perfix-cap-hit`: E_repair retries exhausted on a fix-group AND every remaining group is blocked by it (routes through N23 partial report first via E_halt_partial before emitting halt envelope)

## Multi-File Transactional Semantics (v2.x)

For non-code input types (specification-document, plan-document, skill, prompt), fix-groups may span multiple files. The transactional contract ensures atomicity across all files in a fix-group:

### Transaction Protocol (per fix-group, replaces single-file atomic loop for multi-file groups)

```
1. PRE-STATE CAPTURE:
   a. For each file in the fix-group: capture original content (read into memory)
   b. Record original SHAs for git-tracked files: git hash-object <file>
   c. For new files (skill supporting-file additions): record "new-file" sentinel

2. APPLY ALL EDITS (no git operations between edits):
   a. Apply all Write operations across all files in the fix-group
   b. Track which files were modified and which are new

3. VERIFY ALL:
   a. Run N20 PerFixVerifier against the full set of changed files
   b. Verifier checks correctness, coherence, and cross-file consistency

4. COMMIT OR ROLLBACK (atomic):
   a. ALL VERIFY PASS:
      - git add <all-touched-files>
      - Single commit: git commit -m "[AUDIT-NNN] <summary>" (one commit covers all files in fix-group)
      - For behavioral fixes: add regression-prevention tests in same commit (or paired follow-up)
      - Record all files as applied together

   b. ANY VERIFY FAIL:
      - For each tracked-touched file: git checkout -- <file> (restore original)
      - For each new-file: rm <file> (clean up)
      - Non-git fallback: if git checkout fails (e.g., file not in git repo),
        write pre-state content from step 1a back to the file using Write tool
      - No partial state left on disk
      - Route through E_repair (retry → replan → cap-hit)
```

### Per-Type Transactional Scope

| Input Type | Typical Fix-Group Span | Transactional Behavior |
|-----------|----------------------|----------------------|
| Code | Single file (v1.x) | Single-file commit per finding; unchanged from v1.x |
| Specification document | Single .md file | All edits to the spec doc in one fix-group are committed atomically |
| Plan document | Single .md file | All edits to the plan doc in one fix-group are committed atomically |
| Claude code ai agent skill | Multiple files (SKILL.md + modules/ + schemas/) | All files in the fix-group committed together or rolled back together; multi-file transactional |
| Detailed prompt | Single .md file | All edits to the prompt file in one fix-group are committed atomically |

### Hard Rules (extended for multi-file)

- **Never partial commit** within a multi-file fix-group — all files commit together or none do
- **Never `git revert`** — failed attempts never reach commit, so there's nothing to revert
- **Never bundle** findings across fix-groups in one commit
- **Never `--no-verify`** — hook failures route through E_repair
- **Never amend** prior commits
- **One concern per commit** — even when multi-file, the commit addresses one finding

## Atomic Loop (per fix-group)

```
[FIX-GROUP START]  → manifest write #1: { in_flight_finding_id, pending list updated }

  inner loop (NO manifest writes inside):
    1. Apply edit to working tree (Write tool — no git add yet)
    2. Invoke N20 PerFixVerifier
    3. PASS:
       a. git add <touched-files>
       b. git commit -m "[AUDIT-NNN] <one-line>" (body includes Finding-id, Dimensions, Severity, Source)
       c. For behavioral fixes (not cosmetic): add regression-prevention test in same commit
          (or paired follow-up commit [AUDIT-NNN-test] if language/hook requires separation)
       d. Exit inner loop → fall through to FIX-GROUP END (success)
    4. FAIL:
       a. git checkout -- <tracked-touched-files>
          (if git checkout fails, write pre-state content from memory)
       b. git clean -fd <new-files-created-by-this-attempt>
       c. Record failure_context (failure_class + diagnostic from N20)
       d. E_repair routing:
          - 1st invocation → retry inner loop (with failure context passed to next attempt)
          - 2nd invocation → N17 replan (N17 re-plans the failed fix-group; then retry)
          - 3rd invocation → cap-hit; exit inner loop → fall through to FIX-GROUP END (failure)

[FIX-GROUP END — success]  → manifest write #2: { last_known_good_sha = new commit SHA; finding moved pending → applied }
[FIX-GROUP END — failure]  → manifest write #2: { finding marked failed; downstream-dependent groups → deferred (upstream-dependency-failed); independent groups continue }
```

## Commit Tag Mapping

`F001` → `[AUDIT-001]`, `F042` → `[AUDIT-042]`, `Fnew001` → `[AUDIT-NEW-001]`

## Paired Follow-up Commit Format

Used only when language tooling or a project pre-commit hook rejects bundled test+source commits:
- Primary: `[AUDIT-NNN] <one-line>`
- Follow-up: `[AUDIT-NNN-test] regression test for <one-line>`
- Recorded in fix report as `regression_test_added.deferred_to_followup_commit: <sha>`

## Hard Rules

- **Never `git revert`** — failed fix attempts never reach commit, so there's nothing to revert
- **Never bundle** multiple findings in one commit
- **Never `--no-verify`** — hook failures are treated as `commit-hook-failure`; N20 routes them through E_repair
- **Never amend** prior commits — always new commits, even on retry
- **One concern per commit** — no "while I'm here" cleanups

## Recovery-Manifest Write Policy (cost-aware)

Writes happen ONLY at fix-group boundaries (start, end-success, end-failure). Intra-loop transitions are NOT persisted. If process dies between boundaries, the resume-handler restarts the fix-group from scratch (the atomic loop guarantees no half-applied state in git history).

## Behavioral vs Cosmetic Classification

A fix is **cosmetic** iff its diff modifies only comments, whitespace, or non-semantic renames AND no compiled/interpreted token changes. Cosmetic fixes: `regression_test_added.status: n/a`. All other fixes are **behavioral** and require a regression-prevention test.

## Token Budget

Scales with number of fix-groups and fix complexity. Primary cost: Write operations + git shell commands.

## Backtrack / Aggregation

None (write-serial by design).

## Fan-out Cardinality

Serial 1:1 per fix-group. Write nodes NEVER fan out.

## Back-edge Endpoints

E15: N20 success → N19 (next fix-group).
E_repair: N20 fail → N19 retry (1st invocation); N20 fail → N17 replan then N19 retry (2nd invocation).
