# epiphany-audit SKILL (v2.0.0)

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

**Write-tool footprint:** report files under `~/docs/epiphany/audit/` only; fix diffs against the entire `audit_target` project scope only.

---

## 2. Invocation Contract

```
/epiphany-audit [<path>] [--audit | --fix [<report>] | --improve]
                [--verbose] [--deep]
                [--auto | --confirm-all | --dry-run]
                [--escalate-finding F00N] [--test-cmd '<cmd>']
                [--monorepo-subtree-limit N] [--reverify-state]
                [--full-rerun | --no-rerun]
```

### Mode flags

| Flag | Behavior |
|------|----------|
| `--audit` | Produce report only; do NOT offer fix pipeline (read-only) |
| `--fix [<report>]` | Apply fixes from an audit report. `<report>` optional — if omitted, auto-discovers the most recent audit report for the resolved target. Explicit `<report>` preserves v1.x back-compat. |
| `--improve` | Surface and apply improvements (additive enhancements, optimizations, novel structural moves). Requires a prior audit (or runs one on user confirmation if none exists). |
| (none) | Default: audit → save report → offer to apply fixes. On accept → `--fix`-equivalent; on reject → report preserved as run output. |

### Mode interaction rules (v2.x changes from v1.x)

| Combination | v1.x Behavior | v2.x Behavior |
|-------------|--------------|--------------|
| `--audit` + `--fix` | `halt-on-flag-conflict` | **Sequential:** audit runs first, then fix consumes the resulting report automatically. Valid invocation: `--audit --fix` |
| `--audit` + `--fix <report>` | `halt-on-flag-conflict` | `halt-on-flag-conflict` (unchanged — explicit report bypasses fresh audit, can't combine with `--audit`) |
| `--fix` (no arg) | N/A (new in v2.x) | Auto-discover most recent audit report for resolved target. See `<report>` resolution order below. |
| `--improve` (standalone) | N/A (new in v2.x) | Runs audit prerequisite check; if no report → offers to audit first; then runs improvement subpipeline |
| `--improve` + `--deep` | N/A | Improvement brainstorming with subagent fan-out |

### Autonomy flags (mutually exclusive — unchanged from v1.x)

| Flag | Behavior |
|------|----------|
| `--auto` | Low-risk auto-apply per input-type thresholds; high-risk per-fix confirm |
| `--confirm-all` | Every fix requires per-fix confirmation |
| `--dry-run` | Emit fix-plan + diffs only; no apply, no commits, no branch; pipeline halts at N17 |
| >1 of the above | `halt-on-flag-conflict`; precedence: `--dry-run` > `--confirm-all` > `--auto` |

### Other flags (preserved from v1.x)

| Flag | Behavior |
|------|----------|
| `--verbose` | Adds depth where it improves actionability; never adds nitpick padding |
| `--deep` | Per-input-type deep behavior (see §14). For code: ≤3 spawn budget, subagent fan-out per dimension, interactive B-FIND. For non-code: type-specific deep analysis. |
| `--escalate-finding F00N` | Force finding to high-risk regardless of classification; overrides auto-apply for that finding; `halt-on-invalid-finding-id` if ID not in report |
| `--test-cmd '<cmd>'` | Override auto-detected test command (code type only) |
| `--monorepo-subtree-limit N` | Override cap on distinct project-shaped subtrees (default 10; code type only) |
| `--full-rerun` / `--no-rerun` | Override audit-rerun tier policy; mutually exclusive |
| `--reverify-state` | Clear `reachable: false` annotations from state file at `--fix` entry; valid in `--fix` mode only |

### `<report>` resolution order (for `--fix`)

**Explicit `<report>` (v1.x back-compat path):**
1. Absolute path
2. Path relative to cwd
3. Bare filename or partial slug: search `~/docs/epiphany/audit/` then `fix-reports/`; if no extension, append `.md` and retry
4. Multiple matches → `halt-on-ambiguous-fix-report`
5. No match → `halt-on-unresolvable-fix-report`

**No `<report>` argument (v2.x canonical path):**
1. Resolve the target project (via implied-context resolution, §3)
2. Derive the project slug per input-type slug rules (§13)
3. Search `~/docs/epiphany/audit/` for reports matching the slug pattern, ordered by timestamp descending
4. Zero reports → prompt: "No audit report found for this project. Run the audit first? (y/n)" → on `y`: audit → fix; on `n`: halt
5. Exactly one report → use it
6. Multiple reports → list candidates with timestamps, ask user to select

### Audit-report prerequisite check (mandatory at `--fix` and `--improve` invocation)

Before applying any fix or improvement, the system checks whether a recent audit report exists:

1. Compute current `project_content_sha256` per the hashing scope for the input type (see §11)
2. If report found AND `current_sha256 == report.project_content_sha256` → **recent** — proceed
3. If report found AND `current_sha256 != report.project_content_sha256` → **stale** — prompt: "Audit report is stale (project modified since last audit). Re-run audit before applying fixes? (y/n)" On `y` → re-audit then apply. On `n` → proceed with stale report under user acknowledgment; staleness recorded in run log.
4. If no report found → prompt user to audit first (see resolution order above)
5. If report file missing (SHA-256 captured in metadata but file deleted) → `halt-on-stale-source-report`

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

## 4. Pipeline Diagram (v2.0.0)

```
invoke
  └─ N01 ContextIntake (produces raw project context + resolved_flags)
       └─ N00a AuditabilityPrerequisiteGate
            ├─ FAIL → non-auditability verdict → user
            └─ PASS
                 └─ N00b InputTypeDetector (structural fingerprinting; sets input_type)
                      ├─ classified → routing
                      └─ ambiguous-text → universal-only routing
                           └─ N02 R-ROUTE (loads dimension plugins; consumes input_type;
                                            floor: CORRECTNESS + MAINTAINABILITY always on;
                                            applies per-type section-activation matrix)
                                ├─ N03 B-FIND (E02; per-input-type gap heuristics;
                                │             auto-add HIGH-confidence gaps; --deep: interactive)
                                │    [N03 updates activation map; N04..N09 consume updated map]
                                └─ N04..N09 DimensionAnalyzers (E03 from N02; per updated activation map;
                                          parallel fan-out under --deep)
                                          └─ N10 FPV (false-positive check + location cache; BACKTRACK single cap)
                                               └─ N11 Aggregator (dedup, merge, count-collapse)
                                                    └─ N12 Prioritizer (priority_score, punch list)
                                                         └─ N13 Formatter (markdown per template; emits tetrad on every finding)
                                                              └─ N14 Q-GATE
                                                                   Pass A (mandatory-field + location + CRITICAL/HIGH + no-comment-echo)
                                                                   Pass B (conditional subagent: ≥5 findings OR CRITICAL/HIGH OR --deep)
                                                                   └─ N15 SaveHandler (emits self-audit traces: detector-confidence,
                                                                        section-selector-confidence, tetrad-completeness, two-axis scores,
                                                                        falsifiability survival log)
                                                                        └─ [--improve]: N24 → N25 → N26 → N27 → user (E20)
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
                                └─ N23 FixReporter → N22 RollbackHandler → user
```

### Self-audit trace emission (per run)

The upgraded skill emits per run:
- **detector-confidence trace** — was input-type classification confident? on what fingerprints?
- **section-selector-confidence trace** — which sections activated, which suppressed, why?
- **tetrad-completeness check** — every finding has all 4 tetrad tags
- **two-axis scoring verdict** — creativity ≥7 AND functional-correctness ≥7
- **falsifiability survival log** — which creative findings survived their counter-arguments

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
| N15 | SaveHandler | Emits self-audit traces; resolves report slug per input type (§13) |
| N16 | FixTriage | Added audit-report prerequisite check (recent/stale detection via `project_content_sha256`) |
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
| N23 | FixReporter | fix | formatter |
| N24 | ImprovementContextualizer | improve | analyzer |
| N25 | ImprovementBrainstormer | improve | analyzer |
| N26 | OverEngineeringFilter (OEF) | improve | filter |
| N27 | ImprovementReporter | improve | formatter |

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

For every audit finding tagged "creative" or "novel," the system MUST generate the strongest available counter-argument against its own finding. The finding survives and is emitted only if it withstands the counter-argument.

**Survival check:**
1. Generate counter-argument: what is the strongest case that this finding is a false positive?
2. Evaluate: does the finding's evidence withstand the counter-argument?
3. If yes → emit finding with `falsifiability: survived` and the counter-argument recorded in `falsifiability_counter`
4. If no → drop or downgrade finding; record in falsifiability survival log

```yaml
falsifiability:
  status: "survived"              # survived | downgraded | dropped
  counter_argument: "The -1 offset could be intentional to skip a sentinel token..."
  survival_rationale: "No sentinel token convention is documented; test suite expects N tokens..."
```

---

## 17. Multi-Trial Creativity Tournament

For high-impact findings (severity ≥ HIGH or tagged "creative"), generate 3 alternative framings of the same finding and rank them by:
1. **Actionability** — can the user act on this framing immediately?
2. **Preservation of original intent** — does the framing preserve what the code/doc intends?
3. **Creative leverage** — does the framing open novel improvement paths beyond the immediate fix?

Emit only the top-ranked framing. Trials 2 and 3 are discarded (recorded in run log only).

---

## 18. Two-Axis Scoring Self-Critique (Hard Gate)

Before final artifact emission, the audit pipeline scores its own output on two independent axes:

- **Creativity axis (0–10):** novelty against thin KB, surviving falsification, going beyond known patterns
- **Functional correctness axis (0–10):** passes simulated audit on each of the 5 input types

Both axes must score ≥7 for valid output. Failing either axis triggers regeneration.

Two-axis scoring rubric:

**Creativity:**
- 0–3: recapitulates standard GoT patterns; no novel structural moves
- 4–6: at least one novel structural move (e.g., suppression matrix, prerequisite gate) but conventional execution
- 7–8: multiple novel moves AND each survives a falsification counter-argument
- 9–10: cross-domain synthesis (medical-diagnostic framing, falsifiability-first creativity, tournament ranking) AND every novel move is auditable

**Functional correctness:**
- 0–3: fails simulated audit on ≥3 of 5 input types
- 4–6: passes simulated audit on 3 of 5 input types
- 7–8: passes simulated audit on 4 of 5 input types AND --fix mode validates back-compat on code
- 9–10: passes simulated audit on all 5 input types AND --fix/--improve validates back-compat AND non-auditability verdict path tested

---

## 19. graph.json v2.0.0

`graph.json` is at version `2.0.0` with 29 nodes, 29 edges (5 new: E00a–E00e), N00a/N00b entries, and updated N01/N02/N13/N14/N15 notes fields. See `graph.json` for the authoritative declaration.

---

## 20. Back-Compat Verification Surface

The following v1.x behaviors MUST survive unchanged into v2.x:

1. `--audit` flag on a code project → identical audit pipeline, identical report format (plus tetrad augmentation)
2. `--fix <report>` with explicit report path → identical fix pipeline behavior for code projects
3. Tier-1/Tier-2/Tier-3 classification rules for code → unchanged
4. Autonomy policy matrix for code → unchanged
5. `--dry-run` on code → unchanged
6. Recovery manifest lifecycle → unchanged
7. All v1.x halt states → still fire under identical conditions for code paths
8. `--verbose`, `--deep` (for code), `--escalate-finding`, `--test-cmd`, `--monorepo-subtree-limit`, `--reverify-state`, `--full-rerun`, `--no-rerun` → unchanged for code
9. Report paths for code → unchanged naming scheme
10. Cross-schema invariants for fix-reports → unchanged
11. Q-GATE Pass A / Pass B behavior for code → unchanged
12. Finding `priority_score` formula → unchanged
