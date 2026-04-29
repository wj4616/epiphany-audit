# epiphany-audit SKILL

Graph-of-thought codebase audit + safeguarded fix pipeline.
Family: `epiphany-*`

> **Implementer note:** this file is the Layer-A orchestrator contract. Each node's detailed
> Layer-B contract lives in `modules/N0N-*.md`. JSON schemas are in `schemas/`. Graph
> declaration is in `graph.json`. Dimension plugins are in `dimensions/`.

---

## 1. Purpose & Scope

`epiphany-audit` runs a multidimensional, project-aware audit on any codebase, then
optionally drives a safeguarded fix pipeline. It is designed to:

- Audit for regression areas, bugs, potential issues, and latent problems
- Prune irrelevant dimensions via R-ROUTE (skipped dimensions cite explicit rationale)
- Surface project-specific blindspots via B-FIND
- Cite every finding with verified `file:line` evidence (no hallucinated locations)
- Apply fixes only with explicit per-tier user consent (default policy)
- Track fix state via recovery manifest for safe resumption after interruption
- Optionally generate improvement recommendations via the `--improve` subpipeline

**MAY invoke:** `kb-route` (optional KB consultation via dimension plugins), `prompt-graph` (optional remediation-message enhancement; never required).

**MUST NOT invoke:** `writing-plans`, `executing-plans`, `find-skills`.

**Write-tool footprint:** report files under `~/docs/epiphany/audit/` only; fix diffs against `audit_target` only.

---

## 2. Invocation Contract

```
/epiphany-audit [<path>] [--audit | --fix <report>] [--verbose] [--deep] [--improve]
                [--auto | --confirm-all | --dry-run]
                [--escalate-finding F00N] [--test-cmd '<cmd>']
                [--monorepo-subtree-limit N] [--reverify-state]
                [--full-rerun | --no-rerun]
```

### Mode flags (mutually exclusive)

| Flag | Behavior |
|------|----------|
| `--audit` | Produce report only; do NOT offer fix pipeline |
| `--fix <report>` | Consume existing audit report; run fix pipeline only (skips N01..N15) |
| (none) | Audit → save prompt → fix-offer (default) |
| `--audit` + `--fix` | `halt-on-flag-conflict` |

### Autonomy flags (mutually exclusive)

| Flag | Behavior |
|------|----------|
| `--auto` | Tier-1 silent apply; Tier-2 batch-confirmed; Tier-3 per-fix |
| `--confirm-all` | Every fix requires per-fix confirmation |
| `--dry-run` | Emit fix-plan + diffs only; no apply, no commits, no branch; pipeline halts at N17 |
| >1 of the above | `halt-on-flag-conflict`; precedence on contradiction: `--dry-run` > `--confirm-all` > `--auto` |

### Other flags

| Flag | Behavior |
|------|----------|
| `--verbose` | Adds depth where it improves actionability; never adds nitpick padding |
| `--deep` | Lifts spawn budget to ≤3 (≤4 with `--improve`); subagent fan-out for analyzers; interactive B-FIND prompt; 80k-token checkpoint cap |
| `--improve` | After audit + save prompt, run improvement subpipeline (N24–N27). Valid in audit/no-flag mode only; warning + skip if used with `--fix` |
| `--escalate-finding F00N` | Force finding to Tier-3 regardless of N16 classification; overrides `--auto` for that finding; `halt-on-invalid-finding-id` if ID not in report |
| `--test-cmd '<cmd>'` | Override auto-detected test command |
| `--monorepo-subtree-limit N` | Override cap on distinct project-shaped subtrees (default 10) |
| `--full-rerun` / `--no-rerun` | Override audit-rerun tier policy (§8); mutually exclusive; `halt-on-flag-conflict` if both given |
| `--reverify-state` | Clear `reachable: false` annotations from state file at `--fix` entry; valid in `--fix` mode only |

### `<report>` resolution order (for `--fix`)

1. Absolute path
2. Path relative to cwd
3. Bare filename or partial slug: search `~/docs/epiphany/audit/` then `fix-reports/`; if no extension, append `.md` and retry
4. Multiple matches → `halt-on-ambiguous-fix-report`
5. No match → `halt-on-unresolvable-fix-report`

---

## 3. Implied-Context Resolution

Deterministic, halt-on-ambiguity. **No silent guessing.**

Resolution order:
1. Explicit `<path>` argument wins
2. `--fix <report>` → derives target from `audit_target` in report frontmatter; if both explicit `<path>` AND `--fix <report>` given and `realpath(<path>) != realpath(audit_target)` → `halt-on-target-conflict`
3. `cwd` inside git repo → `git rev-parse --show-toplevel`
4. `cwd` itself
5. `halt-pre-audit`

**Suspicious-target gate** (runs on resolved target regardless of resolution path):

Hard halt (`halt-suspicious-target`) if resolved root is `$HOME`, `/`, `/etc`, `/usr`, `/var`, `/tmp`, or has >5 top-level subdirectories that each independently look like a project.

Warn-and-prompt (soft halt; user may override via `~/.config/epiphany-audit/allowed-roots.json`) for:
- `~/.claude/skills/<x>/`, `~/dotfiles`, `~/.config`, `~/Desktop`, `~/Downloads`

Other ambiguity halts:
- Nested git repos detected → list candidates, ask user
- Session touched multiple projects → list candidates, ask user
- Polyglot monorepo with inconclusive language detection → ask user

---

## 4. Node Registry Overview

27 nodes: 15 audit-pipeline (N01–N15) + 8 fix-pipeline (N16–N23) + 4 improvement subpipeline (N24–N27).

| ID | Name | Active in | Type |
|----|------|-----------|------|
| N01 | ContextIntake | audit | ingest |
| N02 | RelevanceRouter (R-ROUTE) | audit | router |
| N03 | BlindspotFinder (B-FIND) | audit | meta-analyzer |
| N04 | DimensionAnalyzer.CORRECTNESS | audit | analyzer |
| N05 | DimensionAnalyzer.ARCHITECTURE | audit | analyzer |
| N06 | DimensionAnalyzer.PERFORMANCE | audit | analyzer |
| N07 | DimensionAnalyzer.SECURITY | audit | analyzer |
| N08 | DimensionAnalyzer.MAINTAINABILITY | audit | analyzer |
| N09 | DimensionAnalyzer.\<X\> (plugin-instantiated) | audit | analyzer |
| N10 | FalsePositiveVerifier (FPV) | audit | verifier |
| N11 | FindingsAggregator | audit | aggregator |
| N12 | Prioritizer | audit | scorer |
| N13 | ReportFormatter | audit | formatter |
| N14 | Q-GATE (Pass A inline + Pass B conditional subagent) | audit | verifier |
| N15 | SaveHandler | audit | io |
| N16 | FixTriage (F-VAL ingest + Resume-handler + Triage) | fix | validator |
| N17 | FixPlanner | fix | planner |
| N18 | PreFlight | fix | preflight |
| N19 | FixApplier | fix | actuator |
| N20 | PerFixVerifier | fix | verifier |
| N21 | RegressionBattery (battery + tiered audit-rerun) | both | verifier |
| N22 | RollbackHandler | fix | recovery |
| N23 | FixReporter | fix | formatter |
| N24 | ImprovementContextualizer | improve | analyzer |
| N25 | ImprovementBrainstormer | improve | analyzer |
| N26 | OverEngineeringFilter (OEF) | improve | filter |
| N27 | ImprovementReporter | improve | formatter |

For each node's full Layer-B contract see `modules/N0N-*.md`. For the graph declaration see `graph.json`.

---

## 5. Mode Flowcharts

### Audit mode (`--audit` or no-flag)

```
invoke
  └─ N01 ContextIntake
       └─ N02 R-ROUTE (loads dimension plugins; floor: CORRECTNESS + MAINTAINABILITY always on)
            ├─ N03 B-FIND (E02; auto-add HIGH-confidence gaps; --deep: interactive)
            │    [N03 updates activation map; N04..N09 consume the updated map]
            └─ N04..N09 DimensionAnalyzers (E03 from N02; per updated activation map; parallel fan-out under --deep)
                      └─ N10 FPV (false-positive check + location cache; BACKTRACK single cap)
                           └─ N11 Aggregator (dedup, merge, count-collapse)
                                └─ N12 Prioritizer (priority_score, punch list)
                                     └─ N13 Formatter (markdown per §4.1 template)
                                          └─ N14 Q-GATE
                                               Pass A (mandatory-field + location + CRITICAL/HIGH confidence + no-comment-echo)
                                               Pass B (conditional subagent: ≥5 findings OR CRITICAL/HIGH present OR --deep)
                                               └─ N15 SaveHandler
                                                    └─ [--improve]: N24 → N25 → N26 → N27 → user (E20)
                                                    └─ [no-flag]: fix-offer (E21) → N16..N23 fix pipeline
                                                    └─ [--audit]: done (E12 save prompt only)
```

### Fix mode (`--fix <report>` or post-audit fix consent)

```
  └─ N16 FixTriage
       [resume-handler sub-step if prior interrupted run detected]
       F-VAL schema validation → idempotency check → tier classification → grouping + topo-sort
       └─ N17 FixPlanner
            tier batch approval → [--dry-run: write dry-run plan, halt]
            └─ N18 PreFlight
                 orphan sweep → git-state check → baseline capture → branch creation
                 └─ N19 FixApplier (atomic loop per fix-group)
                      └─ N20 PerFixVerifier (targeted tests + type check)
                           [E_repair: 1st→retry N19; 2nd→replan N17; 3rd→cap-hit→N22]
                           └─ N21 RegressionBattery
                                battery (tests/types/lint/build/diff-scope)
                                + tiered audit-rerun (Tier-1: skip; Tier-2: narrow; Tier-3: full)
                                [E_rerun_fail: induced regressions → N16 re-triage]
                                └─ N23 FixReporter (planned termination: partial=false)
                                     └─ E_finalize → N22 RollbackHandler (archive manifest)
                                          └─ E_complete → user
```

### Halt-mid-fix path

```
halt-mid-fix-on-perfix-cap-hit OR halt-mid-fix-on-induced-regression-cap-hit
  └─ E_halt_partial → N23 (partial=true, halt_state=<id>)
       └─ halt envelope → user
       [recovery manifest stays live for resume]
```

---

## 6. Halt-State Envelope Format

Every halt state emits a structured envelope at the **top** of the user-facing message before any diagnostic text:

```
{halt_state: <state-id>, subreason: <text>, diagnostic: <details>}
```

| halt_state | Triggered at | Subreason axis |
|------------|-------------|----------------|
| `halt-pre-audit` | N01 resolution | no resolvable target |
| `halt-suspicious-target` | N01 gate | `$HOME` / wrapper repo / denylist match |
| `halt-ambiguous-target` | N01 resolution | nested git / multi-project / polyglot inconclusive |
| `halt-on-flag-conflict` | N01 parse | mutually exclusive flags |
| `halt-on-flag-rejection` | N01 parse | unsupported flag (e.g., `--demote-finding`) |
| `halt-on-target-conflict` | N01 resolution | explicit path ≠ report's audit_target |
| `halt-on-unresolvable-fix-report` | N16 entry | `<report>` could not be resolved |
| `halt-on-ambiguous-fix-report` | N16 entry | bare `<report>` matched multiple files |
| `halt-on-floor-plugin-missing` | N02 startup | bundled floor plugin file missing; subreason: plugin-name |
| `halt-on-mismatched-version` | N16 F-VAL | tool_version skew; user declined |
| `halt-pre-fix-on-validator-failure` | N16 F-VAL | schema fail / suspicious-content user-declined |
| `halt-on-empty-or-unfixable-report` | N16 ingest | zero main-body findings |
| `halt-on-conflicting-fixes` | N16 triage | incompatible edits on same line range (live mode) |
| `halt-on-test-cmd-unknown` | N18 | no test command available |
| `halt-on-baseline-failure` | N18 | runner crash; subreason: `resume-baseline-missing` |
| `halt-on-git-state-incompatible` | N18 | dirty tree / detached HEAD / no commits; subreason: `branch-name-exhausted` |
| `halt-on-q-gate-failure` | N14 | subreason: `pass-a` / `pass-b` / `pass-b-exec-error` |
| `halt-mid-fix-on-perfix-cap-hit` | E_repair (3rd) | E_repair retries exhausted; all remaining groups blocked |
| `halt-mid-fix-on-induced-regression-cap-hit` | E_repair (post-rerun) | induced-regression fix-group retry cap exhausted |
| `halt-on-scope-creep` | N21 diff-scope | unmapped diff hunks; do NOT auto-revert |
| `halt-on-token-cap` | `--deep` | accumulated context > 80k; partial report emitted |
| `halt-on-recovery-conflict` | run entry | recovery manifest from prior interrupted run |
| `halt-on-user-abort` | any interactive prompt | ctrl-C / explicit halt |
| `halt-on-stale-source-report` | N16 F-VAL | source report file missing or SHA-256 mismatch |
| `halt-no-source-detected` | N01 | binary-only / empty / documentation-only repo |
| `halt-on-files-outside-tree` | N16 F-VAL | report references files outside audit_target tree |
| `halt-on-invalid-finding-id` | N16 post-F-VAL | `--escalate-finding` ID absent from report |
| `halt-on-resume-tree-divergence` | N16 resume-handler | cleanup would discard out-of-scope working-tree changes |

---

## 7. Report Schema Cross-Reference

Five report types; all schema-versioned (`schema_version: 1`). Authoritative JSON schemas in `schemas/`.

| Report type | Output path | Schema file |
|-------------|-------------|-------------|
| Audit report | `~/docs/epiphany/audit/<project-slug>-<YYYYMMDD>-<HHMMSS>.md` | `audit-report-v1.schema.json` |
| Fix report | `~/docs/epiphany/audit/fix-reports/<source-report-id>-fix-<YYYYMMDD>-<HHMMSS>.md` | `fix-report-v1.schema.json` |
| Dry-run plan | `~/docs/epiphany/audit/dry-run-plans/<source-report-id>-dryrun-<YYYYMMDD>-<HHMMSS>.md` | `dry-run-plan-v1.schema.json` |
| Dimension plugin | `dimensions/*.md` (YAML frontmatter only) | `dimension-plugin-v1.schema.json` |
| Improvement report | `~/docs/epiphany/audit/improvement-reports/<project-slug>-<YYYYMMDD>-<HHMMSS>-improve.md` | `improvement-report-v1.schema.json` |

**Cross-schema invariants:**
- `source_report_id` in fix-report = `report_id` in audit-report = `source_report_id` in dry-run plan = `source_report_id` in improvement report.
- `source_audit_report_sha256` verified at `--fix` start; mismatch → `halt-on-stale-source-report`.
- `partial: true ⇔ halt_state: non-null` in fix reports (mutual implication; validated by JSON Schema).
- "Unverified Hypotheses" findings are NOT consumable by `--fix`; F-VAL ingests only main-body findings.
- Improvement reports are read-only artifacts; NOT consumed by `--fix`.

**Finding priority_score formula:**
```
severity:    CRITICAL=4, HIGH=3, MEDIUM=2, LOW=1, INFO=0
confidence:  HIGH=3, MEDIUM=2, LOW=1
effort:      trivial=1, modest=2, significant=3
priority_score = (severity × confidence) / effort
```

**Finding severity definitions:**
```
CRITICAL = data loss, security breach, crash on common path, corruption
HIGH     = crash on edge case, wrong output silently, perf regression >2x
MEDIUM   = degraded UX, recoverable error mishandled, maintainability cliff
LOW      = code smell with concrete future cost
INFO     = observation, no action required
```

---

## 8. Verification-Gate Ordering

Gates run in this fixed order during the fix pipeline. Later gates do not run if an earlier gate fails.

| # | Gate | Node | Failure consequence |
|---|------|------|---------------------|
| 1 | F-VAL ingest | N16 | `halt-pre-fix-on-validator-failure` |
| 2 | Empty-report check | N16 | `halt-on-empty-or-unfixable-report` |
| 3 | Idempotency check | N16 | warn + user override |
| 4 | Tier classification | N16 | defer-on-uncertainty; `halt-on-conflicting-fixes` in live mode |
| 5 | Fix-plan approval | N17 | per-tier outcome (decline = deferred; halt = stop) |
| 6 | Pre-flight baseline | N18 | `halt-on-baseline-failure`, `halt-on-test-cmd-unknown`, `halt-on-git-state-incompatible` |
| 7 | Per-fix verify | N20 | atomic rollback + E_repair routing |
| 8 | Regression battery | N21 (battery sub-step) | E_repair; `halt-on-scope-creep` |
| 9 | Audit-rerun delta | N21 (audit-rerun sub-step) | E_rerun_fail (induced regression) |

**Q-GATE** (audit pipeline):
- Pass A (inline): mandatory fields, location verification (from N10 cache), CRITICAL/HIGH×confidence floor, dup merge, no-comment-echo, no-LOW-only warning
- Pass B (conditional subagent): anti-iatrogenic, evidence-rationale coherence, dimension-classification correctness

**Shared location-verification cache contract (N10 + N14 Pass A):**
- Lives in process memory for one skill invocation only (never persisted)
- Key: `(canonical_file_path, line_range)` normalized as `(start_line, end_line)`
- Value: `{ verified, content_hash, populated_by: "N10", populated_at }`
- N10 FPV is the only writer; N14 Pass A is read-only (falls back to its own Read on cache miss)
- Failed Reads recorded as `verified: false`

---

## 9. Tier + Autonomy Policy

### Tier classification rules (N16, deterministic)

**Tier-1 (mechanical):** ALL of:
- Remediation diff ≤ 2 lines edited within a single file
- No function/method signature changes
- No new identifiers introduced
- Target file imported by ≤ 5 other files
- `confidence: HIGH`
- `effort: trivial`

**Tier-2 (local logic):** ALL of:
- Remediation bounded to a single function body
- May add local symbols (locals, in-scope helper functions)
- No public-API change (no exported identifier renamed/removed/signature-changed)
- Target file imported by ≤ 20 other files

**Tier-3 (cross-cutting):** anything not satisfying Tier-1 or Tier-2, including:
- Multi-file remediation
- Any signature change to an exported identifier
- Schema/migration/config files
- New files
- Findings flagged via `--escalate-finding`
- Non-literal remediation (numbered steps without a literal patch) → Tier-3, `tier_classification_reason: "non-literal remediation"`

### Autonomy policy matrix

| Tier | Default | `--auto` | `--confirm-all` | `--dry-run` |
|------|---------|----------|-----------------|-------------|
| 1 | Batch confirm | Silent apply | Per-fix confirm | No apply |
| 2 | Batch confirm | Batch confirm | Per-fix confirm | No apply |
| 3 | Per-fix confirm | Per-fix confirm | Per-fix confirm | No apply |

**Per-fix-opt-in floor (anti-conformity):** even under `--auto`, any finding with `confidence < HIGH OR effort > trivial` requires per-fix opt-in. Only HIGH-confidence, trivial-effort fixes auto-apply.

**Tier decline behavior:** T1 → T2 → T3 presented in order. Decline on Tier-N → all Tier-N findings `deferred (user-declined-batch)`; pipeline proceeds to Tier-N+1. Explicit `halt` → stop entirely.

**`--demote-finding` is NOT supported** (`halt-on-flag-rejection`). Edit the report manually.

---

## 10. Recovery Semantics

### Recovery manifest lifecycle

Written by N19 at fix-group **boundaries only** (start / end-success / end-failure). NOT written during intra-loop transitions.

**States:**
- `in_flight_finding_id` set → a fix-group is currently executing
- Finding in `applied` → committed successfully
- Finding in `failed` → cap-hit; downstream dependents marked `deferred (upstream-dependency-failed)`
- Finding in `pending` → not yet started

**Planned termination (E_finalize):** N23 writes fix report → N22 reads `fix_report_id` from it → N22 archives manifest to `.recovery/.archive/<report-id>-completed-<ISO-timestamp>.json` → removes live `<report-id>.json` → E_complete → user.

**Halt-mid-fix:** manifest stays live at `~/docs/epiphany/audit/.recovery/<report-id>.json`. Resume on next run.

**Archive states:** `completed` (planned termination), `superseded` (user chose `fresh` over interrupted run), `aborted` (reserved).

### `halt-on-recovery-conflict` options

When a recovery manifest is detected at `--fix` entry:

- **`resume`**: continue from `last_known_good_sha`; skip applied; continue with pending list.
  - Resume-handler sub-step (first action in N16): tree-divergence safety check → `git checkout -- . && git clean -fd` (only after safety check passes or user authorizes) → move `in_flight_finding_id` back to `pending`.
  - Audit-rerun tier policy on resume: determined by combined highest tier (original + resumed run).
- **`fresh`**: archive existing manifest as `superseded-<ISO-timestamp>.json` (forensic record preserved); start over.
- **`abort`**: halt; no changes.

### Idempotency state file

Written by N15 SaveHandler on save-accept. Located at `~/docs/epiphany/audit/.state/<report-id>.json`. Authoritative over git-log for idempotency checks. Conflict resolution:
- `(a) re-apply`: replaces sha in state file; adds `previous_sha_unreachable: <old-sha>` metadata.
- `(b) skip`: annotates state entry with `reachable: false, last_checked: <ISO>`. Cleared by `--reverify-state`.
- `(c) abort`: state file untouched.

---

## 11. Hard Rules (Audit + Fix)

### Audit hard rules

- Every finding has ALL mandatory schema fields (id, location, dimensions, severity, confidence, evidence_excerpt, evidence_excerpt_extended, rationale, remediation, false_positive_check, effort, priority_score, tests_present_signal, provenance). Findings missing any mandatory field → demote to "Unverified Hypotheses".
- Every `file:line` is verified against the actual file via Read at audit time. **No hallucinated lines.**
- Every CRITICAL/HIGH finding has Confidence ≥ MEDIUM. HIGH-severity at LOW-confidence → demote severity OR upgrade confidence with stated evidence.
- LOW-confidence findings include `verify_by: <what would lift confidence>`.
- Duplicate patterns merged with count.
- Q-GATE Pass A no-comment-echo: no finding text quotes the project's own TODO/FIXME without independent verification.
- `tests_present_signal` must be set when test-dir grep matches the involved function/class/module. Elevates the confidence floor for that finding.

### Fix hard rules

- **DO NOT** apply fixes outside source tree.
- **DO NOT** modify files audit didn't flag — **except** regression-prevention test additions in the same commit as the fix (test files containing only new test cases exercising the audit-flagged failure mode).
- **DO NOT** skip post-fix verification.
- **DO NOT** batch-apply fixes spanning the same file without staged review.
- **DO NOT** continue after verification failure without explicit user authorization (or per E_repair bounded retry).
- **Never** expand scope beyond audit findings. Spotted unrelated bug → log as new finding; do not fix it now.
- **Never** bypass safety checks (`--no-verify`, `--force-push`, hook skipping).
- **Never** amend prior commits — always new commits, even on retry.
- **Defer over guess** — if root cause is unclear, mark `deferred` with a question.
- **Idempotent** — re-runs skip already-applied findings (state file > git-log fallback).
- **Fail-loud on partial state** — recovery manifest written at boundaries; mid-flight death leaves coherent at-rest state.

---

## 12. Anti-Patterns

### Audit findings — MUST NOT exhibit

- Stylistic preferences disguised as bugs ("could use `auto` here")
- Findings without reading the actual code (hallucinated `file:line`)
- Generic advice applicable to any project ("add more tests")
- Refactors with no concrete defect or measured cost
- Duplicate findings (collapse with count)
- Wall of LOW-severity nitpicks burying real defects
- Rewrites without a concrete defect driving them
- Echoing project's own TODO/FIXME comments (covered by Q-GATE Pass A no-comment-echo)
- "I would have written it differently" ≠ "this is wrong"
- Reporting findings the existing tests already cover without verifying the test doesn't cover the failure path

### Fix application — MUST NOT exhibit

- Fixes outside source tree
- Modifying files audit didn't flag (except regression-prevention tests in same commit)
- Skipping post-fix verification
- Batch-applying fixes across same file without staged review
- Continuing after verification failure without authorization
- Expanding scope beyond audit findings
- Bypassing safety checks
- Amending prior commits
- Guessing root cause when unclear
- Silent re-application of already-applied findings
- Silent partial state on mid-flight death

---

## 13. Worked Examples

### Example 1 — Worked Finding (full mandatory fields)

```yaml
## Finding F001

id: F001
location: src/parser.py:142
dimensions: [CORRECTNESS]
severity: HIGH
confidence: HIGH
evidence_excerpt: |
  for i in range(len(tokens) - 1):
      emit(tokens[i])
  # final token never emitted
evidence_excerpt_extended: false
rationale: Loop bound drops final token; downstream consumer expects all N tokens.
remediation: |
  -    for i in range(len(tokens) - 1):
  +    for i in range(len(tokens)):
false_positive_check:
  intentional:           { value: false, justification: "no test or comment justifies the -1" }
  file_symbol_verified:  { value: true,  justification: "Read at src/parser.py:140-145" }
  reachable_from_entry:  { value: true,  justification: "called by parse_input in main.py:23" }
  fix_breaks_dependents: { value: false, justification: "grep shows no caller relies on N-1 emission" }
effort: trivial
priority_score: 9.0   # (3 × 3) / 1
verify_by: null
tests_present_signal: false
provenance:
  node: N04
  mode: inline
  model: claude-sonnet-4-6
  pass_b_model: null
  prompt_hash: a3f9e2c1d4b8f7e0a1b2c3d4e5f60718
  plugin_name: null
  plugin_version: null
  audit_rerun_iteration: 0
  q_gate_pass_b_demoted: false
```

### Example 2 — Worked graph.json node entry

```json
{
  "id": "N02",
  "name": "RelevanceRouter",
  "type": "router",
  "mode": "inline",
  "active_in": "audit",
  "inputs": ["project_model from N01", "dimension_plugins_from_disk"],
  "outputs": ["dimension_activation_map", "plugin_registry"],
  "aggregation_policy": "n/a",
  "halt_conditions": ["halt-on-floor-plugin-missing"]
}
```

### Example 3 — Worked improvement entry (post-OEF survivor)

```yaml
## Improvement I002

id: I002
category: quick-win
area: testing
utility_score: 2
cost_score: 1
description: |
  The project uses dynamic test discovery but has no conftest.py at the repo root.
  Failures in fixture setup are silently swallowed on Python < 3.11, meaning a broken
  fixture causes zero tests to run rather than N failures — masking breakage.
action: |
  Add a minimal conftest.py at the repo root with a session-scoped fixture guard:
    assert sys.version_info >= (3, 10), "test suite requires Python 3.10+"
success_measure: |
  Running pytest with a broken fixture produces a visible ERROR line in output
  rather than "collected 0 items".
```

### Example 4 — Worked dimension-routing decision

```
CORRECTNESS:     activated (floor — always on)
MAINTAINABILITY: activated (floor — always on)
PERFORMANCE:     skipped — no hot loops detected, no perf-critical heuristic match
SECURITY:        activated for [shell-injection, secrets-in-source];
                 skipped sub-surfaces [SQL] — no DB layer detected
ARCHITECTURE:    activated — >3 modules with cross-imports detected
```

### Example 5 — Commit message format

```
[AUDIT-001] fix off-by-one in parser token loop

Finding-id: F001
Dimensions: CORRECTNESS
Severity: HIGH
Source: myproject-20260427-100000.md
```

Paired regression-test follow-up commit (if required):
```
[AUDIT-001-test] regression test for fix off-by-one in parser token loop

Test-for-finding: F001
Dimensions: CORRECTNESS
Severity: HIGH
Source: myproject-20260427-100000.md
```
