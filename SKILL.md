# epiphany-audit SKILL (v2.0.3)

Multi-input-type graph-of-thought audit + safeguarded fix pipeline.
Family: `epiphany-*`

> **Implementer note:** this file is the Layer-A orchestrator contract. Each node's detailed
> Layer-B contract lives in `modules/N0N-*.md`. JSON schemas are in `schemas/`. Graph
> declaration is in `graph.json`. Dimension plugins are in `dimensions/`.

---

## 1. Purpose & Scope

`epiphany-audit` runs a multidimensional, project-aware audit on any of 5 input types — code, specification documents, plan documents, Claude Code AI agent skills, and detailed prompts — then optionally drives a safeguarded fix pipeline spanning the full audited project.

- Audit for errors, issues, bugs, potential problems, and areas for improvement across all 5 input types
- Detect input type automatically via structural fingerprinting; route to type-appropriate audit dimensions
- Prune irrelevant dimensions via R-ROUTE (skipped dimensions cite explicit rationale with per-type suppression rules)
- Surface project-specific blindspots via B-FIND with per-input-type gap dimension heuristics
- Cite every finding with verified `file:line` evidence (no hallucinated locations)
- Emit the **medical-diagnostic finding tetrad** on every finding: presenting symptom, underlying cause, prognosis, confidence interval
- Apply fixes only with explicit per-tier / per-input-type user consent (default policy)
- Track fix state via recovery manifest for safe resumption after interruption
- Optionally generate improvement recommendations via the `--improve` subpipeline

**MAY invoke:** `kb-route` (optional KB consultation via dimension plugins), `prompt-graph` (optional remediation-message enhancement; never required).

**MUST NOT invoke:** `writing-plans`, `executing-plans`, `find-skills`, `brainstorming`.

**Write-tool footprint:** report files under `~/docs/epiphany/audit/` only (and only when `--report`/`--reports` given); fix diffs against the entire `audit_target` project scope only.

---

## 2. Invocation Contract

```
/epiphany-audit [<path>] [--audit | --fix [<report>] | --improve]
                [--report | --reports]
                [--verbose] [--deep]
                [--auto | --confirm-all | --dry-run]
                [--escalate-finding F00N] [--test-cmd '<cmd>']
                [--monorepo-subtree-limit N] [--reverify-state]
                [--full-rerun | --no-rerun]
```

### Mode flags

| Flag | Behavior |
|------|----------|
| `--audit` | Produce audit inline; do NOT offer fix pipeline (read-only) |
| `--fix [<report>]` | Apply fixes. `<report>` optional — if omitted, runs a fresh audit first (never loads stale reports). Explicit `<report>` loads that specific saved report. |
| `--improve` | Surface and apply improvements (additive enhancements, optimizations, novel structural moves). Runs a fresh audit first if no report given. |
| (none) | Default: audit inline → offer to apply fixes. No report files written unless `--report`/`--reports` given. |

### Mode interaction rules (v2.x changes from v1.x)

| Combination | v1.x Behavior | v2.x Behavior |
|-------------|--------------|--------------|
| `--audit` + `--fix` | `halt-on-flag-conflict` | **Sequential:** audit runs first, then fix consumes the resulting report automatically. Valid invocation: `--audit --fix` |
| `--audit` + `--fix <report>` | `halt-on-flag-conflict` | `halt-on-flag-conflict` (unchanged — explicit report bypasses fresh audit, can't combine with `--audit`) |
| `--fix` (no arg) | N/A (new in v2.x) | Runs a fresh audit, then applies fixes. Never loads stale reports from disk. |
| `--improve` (standalone) | N/A (new in v2.x) | Runs a fresh audit, then runs improvement subpipeline |
| `--improve` + `--deep` | N/A | Improvement brainstorming with subagent fan-out |
| `--improve` + `--fix` | N/A (new in v2.0.3) | Runs a fresh audit, then fix pipeline, then improvement subpipeline. Valid invocation: `--improve --fix` — the combined form runs all three stages on one fresh audit. |

### Autonomy flags (mutually exclusive — unchanged from v1.x)

| Flag | Behavior |
|------|----------|
| `--auto` | Low-risk auto-apply per input-type thresholds; high-risk per-fix confirm |
| `--confirm-all` | Every fix requires per-fix confirmation |
| `--dry-run` | Emit fix-plan + diffs only; no apply, no commits, no branch; pipeline halts at N17 |
| >1 of the above | `halt-on-flag-conflict`; precedence: `--dry-run` > `--confirm-all` > `--auto` |

### Other flags

| Flag | Behavior |
|------|----------|
| `--report` | Save audit report to `~/docs/epiphany/audit/` (default: skip). Without this flag, audit runs inline and findings are communicated in conversation output only. |
| `--reports` | Save all three reports (audit + fix + improvement) to `~/docs/epiphany/audit/`. Implies `--report`. |
| `--verbose` | Adds depth where it improves actionability; never adds nitpick padding |
| `--deep` | Per-input-type deep behavior (see §14). For code: ≤3 spawn budget, subagent fan-out per dimension, interactive B-FIND. For non-code: type-specific deep analysis. |
| `--escalate-finding F00N` | Force finding to high-risk regardless of classification; overrides auto-apply for that finding; `halt-on-invalid-finding-id` if ID not in report |
| `--test-cmd '<cmd>'` | Override auto-detected test command (code type only) |
| `--monorepo-subtree-limit N` | Override cap on distinct project-shaped subtrees (default 10; code type only) |
| `--full-rerun` / `--no-rerun` | Override audit-rerun tier policy; mutually exclusive |
| `--reverify-state` | Clear `reachable: false` annotations from state file at `--fix` entry; valid in `--fix` mode only |

`--report` and `--reports` are orthogonal to mode flags (combine with any). `--reports` implies `--report`; if both given, `--reports` wins — no conflict.

### `<report>` resolution order (for `--fix`)

**Explicit `<report>` (only way to reuse a saved report):**
1. Absolute path
2. Path relative to cwd
3. Bare filename or partial slug: search `~/docs/epiphany/audit/` then `fix-reports/`; if no extension, append `.md` and retry
4. Multiple matches → `halt-on-ambiguous-fix-report`
5. No match → `halt-on-unresolvable-fix-report`

**No `<report>` argument:** Always runs a fresh audit. Never searches for or loads stale reports from disk. To reuse a saved report, pass it explicitly: `--fix <report>`.

### Audit-report prerequisite check (only when `--fix <report>` with explicit report)

When an explicit `<report>` is given, the system checks whether the report is current:

1. Compute current `project_content_sha256` per the hashing scope for the input type (see §13)
2. If `current_sha256 == report.project_content_sha256` → **recent** — proceed
3. If `current_sha256 != report.project_content_sha256` → **stale** — warn: "Audit report is stale (project modified since last audit). Re-run audit before applying fixes? (y/n)" On `y` → re-audit then apply. On `n` → proceed with stale report under user acknowledgment; staleness recorded in run log.
4. If report file missing (SHA-256 captured in metadata but file deleted) → `halt-on-stale-source-report`

---

## 3. Implied-Context Resolution

Deterministic, halt-on-ambiguity. **No silent guessing.**

Resolution order:
1. Explicit `<path>` argument wins
2. `--fix <report>` → derives target from `audit_target` in report frontmatter; if both explicit `<path>` AND `--fix <report>` given and `realpath(<path>) != realpath(audit_target)` → `halt-on-target-conflict`
3. `cwd` inside git repo → `git rev-parse --show-toplevel`
4. `cwd` itself (may be a single file for spec/plan/prompt types, or a directory for code/skill types)
5. `halt-pre-audit`

**Suspicious-target gate** (runs on resolved target regardless of resolution path):

Hard halt (`halt-suspicious-target`) if resolved root is `$HOME`, `/`, `/etc`, `/usr`, `/var`, `/tmp`, or has >5 top-level subdirectories that each independently look like a project.

Warn-and-prompt (soft halt; user may override via `~/.config/epiphany-audit/allowed-roots.json`) for:
- `~/.claude/skills/<x>/`, `~/dotfiles`, `~/.config`, `~/Desktop`, `~/Downloads`

---

## 3.5 Langfuse Tracing Protocol (MANDATORY — non-blocking)

These Bash commands MUST be called at the exact pipeline events listed below. They are observability hooks — they do NOT alter pipeline behavior, do NOT block execution, and always use `2>/dev/null || true`. Execute each one synchronously at the trigger point then immediately continue the pipeline.

**T1 — Session start. Execute immediately after N00b InputTypeDetector sets `input_type` on `project_model` (before routing to N02).** Substitute: `MODE` = active pipeline mode word (e.g. `audit`, `audit-deep`, `audit-verbose`, `fix`, `improve`); `ITYPE` = classified `input_type` string (e.g. `code`, `specification-document`, `plan-document`, `skill`, `prompt`, or `ambiguous-text`); `TARGET` = first ~150 chars of `project_model.audit_target` collapsed to one line (newlines → spaces, internal `"` escaped as `\"`):
```
python3 ~/.claude/skills/epiphany-audit-v2/scripts/langfuse_tracer.py init --mode "MODE" --input-type "ITYPE" --target "TARGET" 2>/dev/null || true
```

**T2 — Q-Gate complete. Execute immediately after N14 Q-GATE Pass A and Pass B complete (before routing to N15 SaveHandler).** Substitute: `PASSA` = `pass`, `pass-minimal`, or `fail`; `PASSB` = `pass`, `fail`, `exec-error`, `skipped-token-cap`, or `skipped-low-volume`; `CREAT` = integer creativity score 0–10 (use `null` if token-capped); `FC` = integer functional_correctness score 0–10 (use `null` if capped); `TOTAL` = total_findings count; `TETRAD` = tetrad_completeness.tetrad_complete count; `SURVIVED` = falsifiability_survival_log.survived count; `DROPPED` = falsifiability_survival_log.dropped count:
```
python3 ~/.claude/skills/epiphany-audit-v2/scripts/langfuse_tracer.py qgate --pass-a "PASSA" --pass-b "PASSB" --creativity CREAT --functional-correctness FC --total-findings TOTAL --tetrad-complete TETRAD --survived SURVIVED --dropped DROPPED 2>/dev/null || true
```

**T3 — Audit report saved. Execute immediately after N15 SaveHandler completes the save decision.** Substitute: `PATH` = full absolute path of the saved report (empty string `""` if user declined or `--report`/`--reports` not set); `ID` = report_id uuid; `DECISION` = `accepted` or `declined`:
```
python3 ~/.claude/skills/epiphany-audit-v2/scripts/langfuse_tracer.py audit-save --output-path "PATH" --report-id "ID" --save-decision "DECISION" 2>/dev/null || true
```

**T4 — Fix report saved. Execute immediately after N23 FixReporter completes.** Substitute: `FIXPATH` = absolute path of the saved fix report (empty string `""` if `--reports` not set); `VERIFIED` = count of outcomes with status `verified`; `FAILED` = count with status `failed`; `DEFERRED` = count with status `deferred`:
```
python3 ~/.claude/skills/epiphany-audit-v2/scripts/langfuse_tracer.py fix-complete --fix-report-path "FIXPATH" --verified VERIFIED --failed FAILED --deferred DEFERRED 2>/dev/null || true
```

**T5 — Improvement report saved. Execute immediately after N27 ImprovementReporter completes.** Substitute: `IMPROVEPATH` = absolute path of the saved improvement report (empty string `""` if `--reports` not set); `SURVIVORS` = length of the `survivors` array:
```
python3 ~/.claude/skills/epiphany-audit-v2/scripts/langfuse_tracer.py improve-complete --improve-report-path "IMPROVEPATH" --survivors SURVIVORS 2>/dev/null || true
```

---

## 3.6 Audit Report Frontmatter — Canonical Template (REQUIRED)

When a report is saved to disk (under `--report` or `--reports`), it MUST begin with this exact YAML frontmatter. Fields are written by the nodes indicated. This template is also the **primary data source for the Langfuse quality-improvement feedback loop** — the fields marked `[QUALITY SIGNAL]` are the ones that accumulate across runs in Langfuse to reveal whether the skill is improving or regressing.

> **Why this matters:** The two-axis gate (§18), frontmatter-trace coherence check (N14 Pass A #9), and the `--fix` idempotency system (N16) all require these fields to be structurally correct. Getting the template wrong silently breaks these mechanisms.

```yaml
---
# ── Written by N01 + N00b ──
audit_target: "<absolute path or human-readable title>"
input_type: "prompt"             # one of: code | specification-document | plan-document | skill | prompt | ambiguous-text
mode: "audit"                    # pipeline mode word — NOT "audit_mode". Values: audit | audit-deep | fix | improve
skill_version: "epiphany-audit-v2.0.3"
timestamp: "2026-05-03T14:30:00"
project_content_sha256: "<sha256 computed per §13>"

# ── Written by N15 SaveHandler ──
report_id: "<uuid-v4>"           # REQUIRED for --fix idempotency. Generate with:
                                 # python3 -c "import uuid; print(uuid.uuid4())"

# ── Written by N02 RelevanceRouter — dimensions the analyzers ran on ──
dimensions_activated:            # [QUALITY SIGNAL] coverage breadth
  - CORRECTNESS
  - MAINTAINABILITY
  - SECURITY
  - OUTPUT-SCHEMA-COMPLETENESS   # auto-added by B-FIND

gap_dimensions_auto_added:       # [QUALITY SIGNAL] B-FIND blindspot discovery rate
  - OUTPUT-SCHEMA-COMPLETENESS   # empty list [] means B-FIND found no new coverage gaps

# ── Written by N15 from N00b detector_confidence_trace ──
detector_confidence:             # [QUALITY SIGNAL] classification accuracy
  confidence: "high"             # "high" | "marginal" | "ambiguous"
  classified_type: "prompt"      # must match input_type above
  fingerprints:
    - "<key fingerprint observed>"

# ── Written by N15 from N02 section_selector_confidence ──
section_selector_confidence:     # [QUALITY SIGNAL] routing accuracy — shows which dimensions fired and why
  dimensions:
    CORRECTNESS:     {decision: "ACTIVATE", reason: "floor dimension — mandatory for all types"}
    MAINTAINABILITY: {decision: "ACTIVATE", reason: "floor dimension — mandatory for all types"}
    ARCHITECTURE:    {decision: "SUPPRESS", reason: "matrix: S for PROMPT"}
    PERFORMANCE:     {decision: "SUPPRESS", reason: "matrix: S for PROMPT"}
    SECURITY:        {decision: "ACTIVATE", reason: "matrix: A for PROMPT (injection surface)"}

# ── Written by N15 from N14 Q-GATE Pass A check #2 ──
tetrad_completeness:             # [QUALITY SIGNAL] finding completeness rate
  total_findings: 11             # integer count of ### Finding F* headings
  tetrad_complete: 11            # integer count where all 4 tetrad fields are present
  incomplete_ids: []             # list of finding IDs missing any tetrad element

# ── Written by N15 from N14 Q-GATE Pass A check #8 ──
two_axis_scores:                 # [QUALITY SIGNAL] overall quality verdict
  creativity: 8                  # integer 0–10 per §18 rubric; must be ≥7 to pass gate
  functional_correctness: 8      # integer 0–10 per §18 rubric; must be ≥7 to pass gate

two_axis_scores_overridden_by_user: false   # true only if user waived the gate

# ── Written by N15 from N10 FalsePositiveVerifier ──
falsifiability_survival_log:     # [QUALITY SIGNAL] false-positive filter effectiveness
  survived: 9                    # severity ≥ MEDIUM findings that withstood challenge
  downgraded: 1                  # findings whose severity was reduced by falsifiability
  dropped: 1                     # findings eliminated as false positives

# ── Written by N15 from N14 Q-GATE output ──
q_gate:                          # [QUALITY SIGNAL] gate verdicts — REQUIRED, do not omit
  pass_a: "pass"                 # "pass" | "pass-minimal" | "fail" | "skipped-token-cap"
  pass_b: "skipped-low-volume"   # "pass" | "fail" | "exec-error" | "skipped-token-cap" | "skipped-low-volume"
  pass_b_lens: null              # model used for adversarial Pass B, or null if skipped
  pass_b_skip_reason: "fewer than 5 findings and no CRITICAL/HIGH severity"  # null when pass_b ran

# ── Type-specific project_model fields (per §6, insert the block matching input_type) ──
---
```

**Field generation rules:**
- `report_id`: run `python3 -c "import uuid; print(uuid.uuid4())"` during N15 and embed the result
- `mode`: use the resolved pipeline mode word — never use `audit_mode`
- `tetrad_completeness.total_findings`: count of `### Finding F*` headings in the report body
- `tetrad_completeness.tetrad_complete`: count of findings where all 4 fields (presenting_symptom, underlying_cause, prognosis, confidence_interval) are present
- `gap_dimensions_auto_added`: empty list `[]` if B-FIND added no dimensions; otherwise list the added dimension names
- `q_gate.pass_b_skip_reason`: present when `pass_b` is `skipped-*`; `null` when Pass B actually ran
- `falsifiability_survival_log.downgraded`: severity-reduced findings (separate from dropped — do not fold into dropped)

**Quality feedback loop:** Each run's frontmatter feeds the Langfuse trace. Across runs, watch for:
- `two_axis_scores.creativity` trending below 8 → B-FIND or falsifiability analysis weakening
- `gap_dimensions_auto_added` always empty → B-FIND never firing; possible routing issue
- `falsifiability_survival_log.dropped` always 0 → falsifier may not be challenging findings aggressively enough
- `tetrad_completeness.tetrad_complete < total_findings` → finding formation is incomplete
- `q_gate.pass_b` always `skipped-low-volume` → consider running with `--deep` flag more often

---

## 4. Pipeline Diagram (v2.0.3)

```
invoke
  └─ N01 ContextIntake (produces project_model + resolved_flags; input_type=null until N00b feedback)
       └─ N00a AuditabilityPrerequisiteGate
            ├─ FAIL → non-auditability verdict → user
            └─ PASS
                 └─ N00b InputTypeDetector (structural fingerprinting; sets input_type via E00d feedback;
                                            also fans out E_trace_detector → N14 with detector_confidence_trace)
                      └─ N02 R-ROUTE (loads <skill_dir>/dimensions/*.md; section-activation matrix +
                                       plugin-scope gate; floor CORRECTNESS+MAINTAINABILITY always on;
                                       fans out E02 → N03 AND E_trace_section → N14 with section_selector_confidence)
                                └─ N03 B-FIND (E02; per-type gap heuristics; auto-add HIGH-confidence gaps)
                                └─ N04..N09 DimensionAnalyzers (E03 from N02; under --deep, ≤1 shared subagent slot)
                                          └─ N10 FPV (4-question disposition + location cache;
                                                      ALSO falsifiability counter-arguments for severity ≥ MEDIUM,
                                                      aggregated into falsifiability_survival_log;
                                                      fans out E07 → N11 AND E_log_thread → N14)
                                               └─ N11 Aggregator → N12 Prioritizer → N13 Formatter
                                                    └─ N14 Q-GATE (Pass A inline + Pass B conditional subagent)
                                                         Pass A 9 checks (v2.0.2): mandatory-field, tetrad-completeness,
                                                            location, CRITICAL/HIGH × confidence floor, duplicate-merge,
                                                            no-comment-echo, no-LOW-only warning, two-axis hard gate (#8),
                                                            frontmatter-trace coherence (#9)
                                                         Halts: pass-a, pass-b, pass-b-exec-error,
                                                                two-axis-below-threshold, frontmatter-trace-incoherence
                                                         └─ N15 SaveHandler (if --report/--reports: writes report to disk + 6 self-audit frontmatter fields;
                                                                  if not: skips disk write, emits inline summary, sets saved_report_path="")
                                                                  └─ [--improve]: N24 → N25 → N26 → N27 → user (E20)
                                                                  └─ [--improve --fix]: fix-offer (E21) → N16..N23 fix pipeline
                                                                     → N24 → N25 → N26 → N27 → user (E20)
                                                                  └─ [no-flag]: fix-offer (E21) → N16..N23 fix pipeline
                                                                  └─ [--audit]: done
```

### Fix pipeline (unchanged topology, augmented with multi-type project scope)

```
  └─ N16 FixTriage (F-VAL + prerequisite check: recent/stale report)
       └─ N17 FixPlanner (multi-file plan; --dry-run: write plan, halt)
            └─ N18 PreFlight (baseline capture; project-scope)
                 └─ N19 FixApplier (atomic loop per fix-group; multi-file transactional)
                      └─ N20 PerFixVerifier (project-scope verification)
                           └─ N21 RegressionBattery (project-scope battery + audit-rerun)
                                └─ N23 FixReporter (if --reports: writes fix report; else: inline summary only) → N22 RollbackHandler → user
```

### Self-audit trace emission (per run)

The upgraded skill emits per run:
- **detector-confidence trace** — was input-type classification confident? on what fingerprints?
- **section-selector-confidence trace** — which sections activated, which suppressed, why?
- **tetrad-completeness check** — every finding has all 4 tetrad tags
- **two-axis scoring verdict** — creativity ≥7 AND functional-correctness ≥7
- **falsifiability survival log** — counts of severity ≥ MEDIUM findings that survived/downgraded/dropped per their counter-arguments (v2.0.1 scope; was 'creative' tag in v2.0.0)

---

## 5. Node Registry Updates

### New nodes (v2.0.0)

| ID | Name | Active in | Type |
|----|------|-----------|------|
| N00a | AuditabilityPrerequisiteGate | audit | gate |
| N00b | InputTypeDetector | audit | classifier |

### Modified nodes (v2.0.0)

| ID | Name | Change |
|----|------|--------|
| N01 | ContextIntake | Outputs extended: `project_model` now includes `input_type` (set by N00b) and type-specific fields |
| N02 | RelevanceRouter | Consumes `input_type` from project_model; applies per-type section-activation matrix with suppression rules |
| N03 | BlindspotFinder | Per-input-type gap heuristics (see §10) |
| N13 | ReportFormatter | Emits medical-diagnostic finding tetrad on every finding |
| N15 | SaveHandler | Emits self-audit traces; resolves report slug per input type (§13). Writes to disk only under `--report`/`--reports`; otherwise emits inline summary. |
| N16 | FixTriage | Added audit-report prerequisite check for explicit `<report>` only (no-arg `--fix` always runs fresh audit) |
| N17 | FixPlanner | Multi-file plans with per-input-type confirmation thresholds |
| N19 | FixApplier | Multi-file transactional semantics (atomic-commit on success, rollback on partial failure) |

### Deprecated nodes

None. All v1.x nodes preserved. New nodes inserted into the existing ID space at N00a/N00b (before N01 in the logical pipeline, after N01 in the dataflow).

### Complete node registry (v2.0.0)

| ID | Name | Active in | Type |
|----|------|-----------|------|
| N00a | AuditabilityPrerequisiteGate | audit | gate |
| N00b | InputTypeDetector | audit | classifier |
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
| N14 | Q-GATE | audit | verifier |
| N15 | SaveHandler | audit | io |
| N16 | FixTriage | fix | validator |
| N17 | FixPlanner | fix | planner |
| N18 | PreFlight | fix | preflight |
| N19 | FixApplier | fix | actuator |
| N20 | PerFixVerifier | fix | verifier |
| N21 | RegressionBattery | both | verifier |
| N22 | RollbackHandler | fix | recovery |
| N23 | FixReporter | fix | formatter (writes to disk only under --reports) |
| N24 | ImprovementContextualizer | improve | analyzer |
| N25 | ImprovementBrainstormer | improve | analyzer |
| N26 | OverEngineeringFilter (OEF) | improve | filter |
| N27 | ImprovementReporter | improve | formatter (writes to disk only under --reports) |

---

## 6. Updated N01 ContextIntake — project_model Per Input Type

The upgraded N01 produces a `project_model` whose shape varies by detected `input_type`.

**Universal fields** (present for all types):

```yaml
audit_target: string
input_type: string                 # set by N00b InputTypeDetector
file_count: integer
total_lines: integer
git_state:
  head: string
  dirty: boolean
  branch: string | null
  detached: boolean
  has_commits: boolean
contained_types: string[]          # types of sub-artifacts found (empty if none)
contained_artifacts:               # details on nested artifacts
  - type: string
    line_range: [integer, integer]
    depth: integer
```

**Type-specific fields:**

### Code (`input_type: "code"`)
```yaml
language_summary: { [lang]: integer }
build_manifest: string | null
test_command: string | null
entry_points: string[]
project_type: string[]
is_monorepo: boolean
subtrees: SubtreeDescriptor[]
```
(Unchanged from v1.x — existing fields preserved verbatim.)

### Specification Document (`input_type: "specification-document"`)
```yaml
heading_hierarchy:
  depth_max: integer
  heading_map: { [depth]: integer }     # depth → count of headings at that depth
requirement_blocks_count: integer
acceptance_criteria_count: integer
has_rationale_sections: boolean
embedded_code_block_count: integer
spec_authoring_skill: string | null     # "brainstorming" if provenance markers detected
```

### Plan Document (`input_type: "plan-document"`)
```yaml
phase_count: integer
phase_ids: string[]
checkpoint_count: integer
dependency_graph:
  [phase_id: string]: string[]          # phase → list of phase IDs it depends on
task_list_count: integer
has_rollback_procedure: boolean
plan_authoring_skill: string | null     # "writing-plans" if provenance markers detected
```

### Claude Code AI Agent Skill (`input_type: "skill"`)
```yaml
skill_name: string
has_frontmatter: boolean
frontmatter_fields: string[]
supporting_file_count: integer
module_count: integer
has_tests: boolean
language_summary: { [lang]: integer }   # for supporting code files only
skill_directory: string
```

### Detailed Prompt (`input_type: "prompt"`)
```yaml
tag_topology:                           # tag → depth in XML tree
  [tag_name: string]: integer
meta_source: string | null              # value of <meta source="..."/>
has_output_format: boolean
has_verification: boolean
has_edge_cases: boolean
embedded_schema_count: integer
prompt_authoring_skill: string | null   # "prompt-graph" or "prompt-cog" if provenance detected
```

### Ambiguous Text (`input_type: "ambiguous-text"`)
```yaml
observed_fingerprints: string[]         # fingerprints the detector observed
detector_confidence: number             # float 0–1; the primary type's score
all_type_scores:                        # scores for all 5 types
  code: number
  specification-document: number
  plan-document: number
  skill: number
  prompt: number
```
Minimal model; only universal audit sections activate.

---

## 7. Section-Activation Matrix (with Suppression Rules)

Rows = built-in audit dimensions + universal sections. Columns = 5 input types + ambiguous-text. Cells: A=ACTIVATE, S=SUPPRESS, C=CONDITIONAL (condition noted).

```
DIMENSION              | CODE  | SPEC  | PLAN  | SKILL | PROMPT | AMBIGUOUS
-----------------------+-------+-------+-------+-------+--------+----------
CORRECTNESS (floor)    |   A   |   A   |   A   |   A   |   A    |    A
MAINTAINABILITY (floor)|   A   |   A   |   A   |   A   |   A    |    A
ARCHITECTURE           |   A   | C(a)  | C(b)  | C(c)  |   S    |    S
PERFORMANCE            |   A   |   S   |   S   | C(d)  |   S    |    S
SECURITY               |   A   | C(e)  |   S   |   A   |   A    |    C(f)
```

Condition notes:
- **(a)** ARCHITECTURE on SPEC: ACTIVATE if spec spans ≥3 subsystems or defines inter-component contracts; else SUPPRESS.
- **(b)** ARCHITECTURE on PLAN: ACTIVATE if plan has ≥3 phases with cross-phase dependencies; else SUPPRESS.
- **(c)** ARCHITECTURE on SKILL: ACTIVATE if skill directory has ≥3 modules or references subagent orchestration; else SUPPRESS.
- **(d)** PERFORMANCE on SKILL: ACTIVATE if SKILL.md specifies token budgets or latency constraints; else SUPPRESS.
- **(e)** SECURITY on SPEC: ACTIVATE if spec defines auth, data handling, or user-input boundaries; else SUPPRESS.
- **(f)** SECURITY on AMBIGUOUS: ACTIVATE only universal-injection-surface checks; SUPPRESS language-specific vulnerability scans.

---

## 8. Per-Dimension Cross-Type Finding-Class Suppression Rules

Extends the matrix above with finding-class granularity:

| Finding class | CODE | SPEC | PLAN | SKILL | PROMPT |
|---------------|---|---|---|---|---|---|
| race-condition / deadlock | A | S | S | C(g) | S |
| missing-test-coverage | A | C(h) | S | A | S |
| phase-ordering-inconsistency | S | C(i) | A | C(i) | S |
| prompt-injection-surface | S | C(j) | S | A | A |
| schema-drift | S | A | A | A | A |
| structural-contradiction (doc says X then says ¬X) | S | A | A | A | A |
| missing-rollback-procedure | S | S | A | C(k) | S |
| undefined-acceptance-criteria | S | A | S | S | S |
| technique-application-inconsistency | S | S | S | S | A |
| build-config-integrity | A | S | S | S | S |
| dependency-cycle | A | C(l) | A | C(m) | S |
| kb-route-query-staleness | S | S | S | A | S |
| output-format-underspecification | S | A | A | A | A |

Condition notes:
- **(g)** SKILL concurrency: only if SKILL.md or supporting modules reference concurrency, threading, or async patterns.
- **(h)** SPEC test-coverage: only if spec defines testable acceptance criteria with concrete pass/fail predicates.
- **(i)** phase-ordering on SPEC/SKILL: only if document has explicit sequential/phase structure.
- **(j)** SPEC injection: only if spec defines user-facing input fields or prompt templates.
- **(k)** SKILL rollback: only if skill writes files (has a write-tool footprint).
- **(l)** SPEC dependency-cycle: only if spec defines multi-component dependency graph.
- **(m)** SKILL dependency-cycle: only if skill has ≥3 modules with cross-references.

---

## 9. Medical-Diagnostic Finding Tetrad

Every audit finding the upgraded skill produces MUST carry all four tetrad fields. The tetrad AUGMENTS the existing v1.x mandatory fields — it does NOT replace them.

**Existing mandatory fields (preserved from v1.x):**

```yaml
id, location, dimensions, severity, confidence, evidence_excerpt,
evidence_excerpt_extended, rationale, remediation, false_positive_check,
effort, priority_score, tests_present_signal, provenance
```

**Tetrad fields (new in v2.x):**

```yaml
# (a) Presenting symptom — observable manifestation (distinct from evidence_excerpt)
presenting_symptom: string

# (b) Underlying cause — root mechanism (distinct from rationale; strictly the mechanism)
underlying_cause: string

# (c) Prognosis — forward-looking consequence if unfixed (distinct from severity label)
prognosis: string

# (d) Confidence interval — quantified confidence [lower, upper] both 0.0–1.0
confidence_interval: [number, number]
```

**Tetrad field constraints:**
- `confidence_interval` width reflects evidence strength — narrower = more evidence; midpoint reflects finding confidence
- Findings missing any element of the tetrad are considered malformed and must be regenerated
- The categorical `confidence` field (HIGH/MEDIUM/LOW) remains alongside the interval — the interval provides resolution the category cannot

**Worked example — full finding with tetrad:**

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
priority_score: 9.0
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

# --- v2.x tetrad (augments, does not replace) ---
presenting_symptom: "Token loop terminates one element early; final token silently dropped from output stream."
underlying_cause: "Off-by-one error in loop bound — `range(len(tokens) - 1)` instead of `range(len(tokens))`."
prognosis: "Downstream consumers expecting N tokens silently receive N-1 tokens. If the final token is a terminator, the consumer hangs. If it's a data payload, the consumer produces incomplete results with no error signal."
confidence_interval: [0.90, 0.99]   # narrow interval: code is unambiguous, evidence is direct
```

---

## 10. B-FIND Gap-Dimension Taxonomy Per Input Type

The blindspot finder (N03) detects dimensions the user didn't explicitly request but which the input type's structure implies are relevant.

### Code (v1.x heuristics, unchanged)
- WEB-ACCESSIBILITY (web projects serving HTML)
- I18N (localized strings detected)
- DOCUMENTATION (public API with no docstrings)
- Existing HIGH-confidence auto-add threshold: 2+ independent heuristics agree

### Specification Document
| Gap Dimension | Candidate Condition | HIGH-confidence Auto-add Threshold |
|---------------|-------------------|-----------------------------------|
| REQUIREMENT-COMPLETENESS | Spec has requirements without corresponding acceptance criteria | ≥5 requirement blocks AND 0 acceptance criteria |
| CROSS-REFERENCE-INTEGRITY | Spec references other sections | ≥3 cross-references detected |
| ACCEPTANCE-CRITERIA-TESTABILITY | Acceptance criteria lack concrete pass/fail predicates | ≥3 criteria with no verifiable predicate |
| DOMAIN-CONSISTENCY | Terminology drift across sections | Same concept named differently in ≥2 sections |

### Plan Document
| Gap Dimension | Candidate Condition | HIGH-confidence Auto-add Threshold |
|---------------|-------------------|-----------------------------------|
| RISK-ASSESSMENT | Plan has no risk section | "risk"/"rollback" mentioned in ≤1 location |
| ROLLBACK-PROCEDURE | Plan lacks rollback steps | `has_rollback_procedure: false` AND ≥3 phases |
| DEPENDENCY-TRACEABILITY | Cross-phase dependencies not explicitly mapped | ≥5 phase dependencies detected |
| ESTIMATE-CALIBRATION | Task effort estimates absent or uncalibrated | ≥10 tasks with no effort markers |

### Claude Code AI Agent Skill
| Gap Dimension | Candidate Condition | HIGH-confidence Auto-add Threshold |
|---------------|-------------------|-----------------------------------|
| MODULE-COHERENCE | Multi-module skill without interface docs | ≥3 modules detected |
| TOKEN-BUDGET-COMPLIANCE | Skill mentions token budgets | SKILL.md contains "token" keyword |
| KB-QUERY-FRESHNESS | Skill queries KBs | `kb_route_query` set on any dimension |
| SKILL-REGISTRATION-CONSISTENCY | Skill name/path mismatches across references | Skill name differs in ≥2 locations |

### Detailed Prompt
| Gap Dimension | Candidate Condition | HIGH-confidence Auto-add Threshold |
|---------------|-------------------|-----------------------------------|
| VERIFICATION-SCAFFOLDING | Prompt has task/output-format but no verification | `<task>` and `<output_format>` present but no `<verification>` |
| OUTPUT-SCHEMA-COMPLETENESS | Prompt defines structured output | Structured output schema detected |
| TECHNIQUE-APPLICATION | Prompt references techniques | `<meta source="..."/>` references prompt-graph |
| CONSTRAINT-SATURATION | Prompt has constraints but some edge cases unhandled | ≥5 constraints but no `<edge_cases>` section |

Under `--deep`, all gap candidates are offered interactively regardless of confidence.

---

## 11. Multi-Type Classification Precedence Rules

When the detector reports a multi-type classification (e.g., 60% plan-document, 40% specification-document):

1. **UNION rule** — if ANY detected type says A for a dimension → dimension is ACTIVATED. Rationale: it's worse to miss a real finding than to emit an inapplicable one (the tetrad confidence interval flags applicability risk).
2. **SUPPRESSION-OVERRIDE rule** — a finding class is emitted only if NOT marked S for the PRIMARY type.
3. Example: input is 60% plan, 40% spec → primary=plan. "Phase-ordering-inconsistency" is A for plan → emitted. "Undefined-acceptance-criteria" is A for spec but S for plan → SUPPRESSED (plan is primary). "Structural-contradiction" is A for both → emitted.
4. CONDITIONAL cells evaluate; if condition met for any detected type → dimension activates.
5. DUAL-PRIMARY tie (two types at equal confidence, both above threshold) → primary is the type with more ACTIVATE cells in the matrix. Tie-breaking recorded in detector-confidence trace.

---

## 12. Runtime Mode Design — `--fix` and `--improve` Edit Scope

### `--fix [<report>]` — Apply Audit Findings

Implements solutions based on audit findings. Edit scope spans **the entire project being audited** — NOT a single representative file.

- **Code:** source files, tests, configuration — multi-file edits as required
- **Specification document:** structural reorganization, content additions, requirement clarifications, removal of contradictions, missing-section insertion
- **Plan document:** phase reordering, dependency corrections, checkpoint additions, task list updates, missing-rollback-procedure additions
- **Claude code ai agent skill:** SKILL.md AND supporting files (modules, KB, scripts, agent definitions, examples) — the entire skill directory
- **Detailed prompt:** prompt body, frontmatter, embedded schemas, technique applications, verification scaffolding

### `--improve` — Apply Improvement Findings

Surfaces and applies improvements (additive enhancements, optimizations, novel structural moves) rather than corrections (defect fixes). Same project-scope edit semantics as `--fix`. Same audit-report prerequisite check applies.

### Multi-file Edit Transactional Semantics

```
For each fix-group in topo_sorted_order:
  1. Capture pre-state (file contents + hashes for all files in group)
  2. Apply all edits in the group
  3. Run per-fix verifier
     ├─ PASS → commit group; write recovery manifest at boundary
     └─ FAIL → rollback group to pre-state; route through E_repair
```

**Atomic-commit:** all edits in a fix-group are committed together as a single git commit.

**Rollback on partial failure:** if any edit in a fix-group fails verification, the entire group is rolled back to pre-state. Individual file rollbacks use the pre-state content hashes captured at step 1.

### Dry-run Preview Mode (`--dry-run`)

Pipeline halts at N17 FixPlanner. Output:
- List of planned edits per file (unified diff format)
- Per-fix-group risk classification
- Files that would be touched
- No filesystem modifications, no commits, no branch creation

### User Confirmation Thresholds Per Input Type

Auto-apply without confirmation when ALL criteria for the input type are met:

| Input Type | Low-Risk (auto-apply) | High-Risk (require confirmation) |
|-----------|----------------------|--------------------------------|
| Code | Tier-1: ≤2 lines, single file, no signature change, confidence=HIGH, effort=trivial (v1.x unchanged) | Tier-2 and Tier-3 (v1.x unchanged) |
| Specification document | Single-section addition only, no removal of existing content, no heading hierarchy restructuring | Any removal, heading restructuring, multi-section edits, or acceptance-criteria rewrites |
| Plan document | Checkpoint addition (new checkpoint only, no reordering), task-list append (new tasks only), or missing-rollback-procedure addition | Phase reordering, dependency corrections, task removal, any edit touching existing phase structure |
| Claude code ai agent skill | YAML frontmatter field addition only (new field, no existing-field modification), or supporting-file addition (new file, no existing-file edits) | Any SKILL.md prose modification, existing frontmatter field changes, supporting-file modifications, module edits |
| Detailed prompt | `<meta>` tag addition, output-format addition (new section, no existing-format modification), or verification-scaffolding addition | Prompt body modifications, frontmatter changes, embedded schema changes, technique-application modifications |

These thresholds override the existing tier system for non-code types. For code, the existing v1.x tier system (§9 of original SKILL.md) remains authoritative and unchanged.

### Back-Compat with v1.x `--fix` Single-File Flow

The existing code path — `--fix <report>` where `<report>` is an audit report on a code project — produces identical behavior to v1.x. The tier system, autonomy policy, per-fix-opt-in floor, and halt-state envelope are all preserved unchanged.

---

## 13. Report Path and Project-Slug Resolution Per Input Type

All reports land in `~/docs/epiphany/audit/`.

| Input Type | Slug Derivation | Example |
|-----------|-----------------|---------|
| Code | `basename(git_toplevel \| cwd)` (v1.x) | `CogVST-20260429-143000.md` |
| Specification document | `basename(file, '.md')-spec` | `enhanced-vst-playbook-spec-20260429-143000.md` |
| Plan document | `basename(file, '.md')-plan` | `migration-plan-20260429-143000.md` |
| Claude code ai agent skill | `basename(skill_dir)-skill` | `epiphany-audit-skill-20260429-143000.md` |
| Detailed prompt | `basename(file, '.md')-prompt` (strip date prefixes when redundant) | `prompt-graph-design-audit-orchestration-prompt-20260429-143000.md` |

### `project_content_sha256` Hashing Scope Per Input Type

Stored in audit report frontmatter at audit time. Used at `--fix` invocation for recency/staleness detection.

| Input Type | Hashing Scope |
|-----------|---------------|
| Code | `git ls-tree -r HEAD \| sha256sum` (if git repo); else `find . -type f -not -path './.git/*' -exec sha256sum {} \; \| sort \| sha256sum` |
| Spec/Plan/Prompt (single-file) | `sha256sum <file>` |
| Skill (directory) | `find <skill-dir> -type f -exec sha256sum {} \; \| sort \| sha256sum` |

---

## 14. `--deep` Semantics Per Input Type

| Input Type | `--deep` Behavior |
|-----------|------------------|
| Code | Unchanged from v1.x: ≤3 spawn budget (≤4 with `--improve`), subagent fan-out per dimension, interactive B-FIND, 80k token checkpoint cap |
| Specification document | Cross-reference validation (verify every "see Section X" reference resolves), acceptance-criteria completeness check against requirements, KB consultation for domain best-practices if `kb_route_query` is set |
| Plan document | Dependency-graph cycle detection, phase-ordering constraint validation, checkpoint-to-task coverage mapping, interactive gap-dimension prompt for missing plan sections |
| Claude code ai agent skill | Subagent fan-out per module (each analyzed independently), cross-module consistency check (module A's output != module B's expected input), KB consultation for skill-design best-practices |
| Detailed prompt | Prompt-graph topology deep-traversal (verify every `<meta source="..."/>` reference resolves), technique-application cross-validation (does the prompt actually apply what it claims to apply?), structured-output schema validation |

---

## 15. Dimension Plugin `applies_to.input_types` Extension

Existing dimension plugins use `applies_to.languages` and `activation_triggers` — both code-oriented. For a plugin to activate on non-code input types, add an optional `applies_to.input_types` field:

```yaml
applies_to:
  languages: [cpp]             # existing, unchanged
  input_types:                 # NEW — if absent, defaults to [code] (back-compat)
    - code
    - specification-document
    - plan-document
    - skill
    - prompt
```

A plugin that omits `input_types` defaults to `[code]` only — preserving back-compat for all existing dimension plugins. A plugin listing additional types activates with `activation_triggers` reinterpreted per type (e.g., `import_grep` on a spec doc searches for concept references, not language imports).

---

## 16. Falsifiability-First Creativity Check

For every audit finding with **severity ≥ MEDIUM** (i.e., MEDIUM, HIGH, or CRITICAL), the system MUST generate the strongest available counter-argument against its own finding. The finding survives and is emitted only if it withstands the counter-argument.

**Scope rule (v2.0.1):** the falsifiability check fires on severity (objective, present on every finding) rather than on a `creative`/`novel` tag (no analyzer produced such a tag in v2.0.0). This matches the practice already shown in `tests/schema-validation/fixtures/valid_audit_report.json` where the canonical fixture applies falsifiability to a HIGH-severity finding. INFO and LOW severities skip the check (cost vs. value).

**Producer of the check:** N10 FalsePositiveVerifier — see N10 module contract. N10 has source-file Read access (already used for location verification), so it can construct stronger counter-arguments than N13 could from Finding prose alone. N13 only renders the resulting `falsifiability` block in the report.

**Survival check (executed in N10):**
1. Generate counter-argument: what is the strongest case that this finding is a false positive? Use both the finding's `evidence_excerpt` AND a fresh Read of up to 2-3 lines of context around `location` if not already in the location_verification_cache.
2. Evaluate: does the finding's evidence withstand the counter-argument?
3. If yes → emit finding with `falsifiability.status: "survived"` and counter-argument recorded in `falsifiability.counter_argument`; rationale in `falsifiability.survival_rationale`.
4. If no → either drop the finding (if the counter-argument is decisive) or downgrade severity by one tier; record outcome in N10's contribution to the falsifiability survival log.

```yaml
falsifiability:
  status: "survived"              # survived | downgraded | dropped
  counter_argument: "The -1 offset could be intentional to skip a sentinel token..."
  survival_rationale: "No sentinel token convention is documented; test suite expects N tokens..."
```

---

## 17. Multi-Trial Creativity Tournament

For high-impact findings (severity ≥ HIGH), generate 3 alternative framings of the same finding and rank them by:
1. **Actionability** — can the user act on this framing immediately?
2. **Preservation of original intent** — does the framing preserve what the code/doc intends?
3. **Creative leverage** — does the framing open novel improvement paths beyond the immediate fix?

Emit only the top-ranked framing. Trials 2 and 3 are discarded (recorded in run log only).

---

## 18. Two-Axis Scoring Self-Critique (Hard Gate)

Before final artifact emission, the audit pipeline scores its own output on two independent axes:

- **Creativity axis (0–10):** novelty against thin KB, surviving falsification, going beyond known patterns
- **Functional correctness axis (0–10):** passes simulated audit on each of the 5 input types

Both axes must score ≥7 for valid output. Failing either axis halts the pipeline at N14 with `halt-on-q-gate-failure` (subreason: `two-axis-below-threshold`); the user is shown the failing scores with rationale and may either accept the report under explicit override (recorded in run log) or regenerate.

**Producer:** N14 Q-GATE Pass A check #8. N14 computes both scores against the rubric below, stores them as a top-level `two_axis_scores` field on the validated_report, and gates emission to N15.

**Override:** under `--auto`, a single failure of the gate halts; under `--confirm-all` or `--dry-run`, the user is prompted with the failing rationale and may waive the gate (the waiver is recorded as `two_axis_scores_overridden_by_user: true` in the report frontmatter).

Two-axis scoring rubric: see N14 module §"Two-Axis Score Computation Rubric (v2.0.2 — mechanical)" for the authoritative computable predicates. Two implementations evaluating the same report MUST produce identical scores. Summary:

- **Creativity** sums points across deterministic predicates over `tetrad_completeness`, `falsifiability_survival_log`, `dimensions_activated`, `gap_dimensions_auto_added`, `section_selector_confidence`, and finding-body fields.
- **Functional correctness** sums points across schema-validity, q_gate state, detector confidence, location-cache verification, floor-dimension presence, frontmatter-trace coherence, tetrad completeness, and CRITICAL/HIGH × confidence floor.

The threshold (≥7 each axis) is calibrated so a well-formed report with full tetrad coverage and full falsifiability coverage scores ≥7 on creativity; a schema-validating report with verified locations and coherent traces scores ≥7 on functional correctness. Reports failing schema validation cannot pass the gate.

---

## 19. graph.json v2.0.2

`graph.json` is at version `2.0.3` with 29 nodes and 40 edges. v2.0.0 introduced E00a–E00e + the E13 chain + E_repair / E_rerun_fail / E_diffscope / E_finalize / E_complete / E_halt_partial / E15 / E16–E21. v2.0.2 added three side-channel edges: E_trace_detector (N00b → N14), E_trace_section (N02 → N14), E_log_thread (N10 → N14) — wiring N14's documented inputs through the graph rather than via implicit context-passing. The `conventions` block documents propagation rules and runtime-enforced caps. See `graph.json` for the authoritative declaration.

---

## 20. Back-Compat Verification Surface

The following v1.x behaviors are preserved into v2.x; **v2.0.x changes that fire on code paths** are called out explicitly so implementations don't read v1.x behavior into the spec where v2 has updated it.

1. `--audit` flag on a code project → v1.x audit pipeline preserved; report format augmented with v2.x tetrad and v2.0.1+ self-audit frontmatter fields (additive; v1.x parsers ignore unknown frontmatter)
2. `--fix <report>` with explicit report path → v1.x fix pipeline preserved; v2.0.1 added recovery-conflict detection at fix-mode entry (fires on code paths)
3. Tier-1/Tier-2/Tier-3 classification rules for code → unchanged
4. Autonomy policy matrix for code → unchanged
5. `--dry-run` on code → v1.x preserved; v2.0.1 N17 emits a warning when `--no-rerun`/`--full-rerun` is also set under `--dry-run` (cosmetic only)
6. Recovery manifest lifecycle → unchanged
7. v1.x halt states → still fire under v1.x conditions; **new halt states added in v2.x that ALSO fire on code paths**: `halt-on-recovery-conflict` (v2.0.1), `halt-on-q-gate-failure` subreasons `two-axis-below-threshold` and `frontmatter-trace-incoherence` (v2.0.1), `halt-pre-fix-on-validator-failure` subreason `suspicious-content-rejected` (v2.0.1)
8. `--verbose`, `--deep` (for code), `--escalate-finding`, `--test-cmd`, `--monorepo-subtree-limit`, `--reverify-state`, `--full-rerun`, `--no-rerun` → unchanged for code; v2.0.2 adds `--max-fix-group-size`, `--max-merge-depth`, `--skip-verification-tool` for non-code (no-op on code)
9. Report paths for code → unchanged naming scheme
10. Cross-schema invariants for fix-reports → unchanged
11. Q-GATE for code → Pass A grew from 7 v1.x checks to **9 checks in v2.0.1** (added: tetrad-completeness #2, two-axis hard gate #8, frontmatter-trace coherence #9). Pass B unchanged. The two new gates fire on code paths. Implementations following v1.x Pass A semantics will under-implement; consult N14 module contract for the v2.0.2 authoritative list.
12. Finding `priority_score` formula → unchanged
