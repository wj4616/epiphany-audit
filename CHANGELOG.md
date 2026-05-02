# Changelog

## [2.0.3] — 2026-04-29

Self-audit improve+fix pass. Closes 4 findings (1 HIGH, 1 MEDIUM, 2 LOW). Total test count: 175 → 189.

### Fixed (HIGH)

- **F001** — Created `tests/integration/test_two_axis_scoring.py`: implements `TwoAxisScorer` reference scorer for the two-axis rubric (14 tests: determinism × 2, creativity predicates × 5, functional-correctness predicates × 4, gate threshold × 3). Updated `modules/N14-q-gate.md:103` reference to confirm the file exists and describe what it provides.

### Fixed (MEDIUM)

- **F002** — Rewrote `graph.json` `conventions.spawn_cap` to explicitly state the ≤3/≤4 numbers are TOTAL subagent ceilings, broken down by contributor: dim-batch (1), N14-PassB (1), N21-rerun (1), N25-phase2 (1 if --improve).

### Fixed (LOW)

- **F003** — Added algorithm note to `modules/N16-fix-triage.md` Conflicting Edits Definition: O(n²) naive is acceptable (n<50 per file); sweep-line/interval-tree for larger sets.
- **F004** — Added `halt_condition_naming` convention to `graph.json`: documents the `halt-<timing>-<condition>` pattern and valid timing prefixes (on/pre/mid/suspicious/ambiguous/no).

### Changed

- graph.json: version bumped to 2.0.3; conventions block extended with `halt_condition_naming`; `spawn_cap` rewritten with explicit total-ceiling breakdown
- N14 module: line 103 reference updated (file now exists)
- N16 module: algorithm note appended to Conflicting Edits Definition

### Self-Audit-Improver Pass (7 proposals applied 2026-04-29)

- **[Proposal 2 — BUG][MEDIUM]** All 5 dimension plugin prompts updated from code-oriented to input-type-agnostic: each `prompt_template` now declares `input_type` via `{{input_type}}` placeholder and provides per-type analysis guidance (code, spec/plan-doc, skill, prompt).
- **[Proposal 3 — STRUCTURAL][MEDIUM]** `schema_version` bumped from 1 → 2 in all 5 JSON schemas (`audit-report-v1`, `dimension-plugin-v1`, `dry-run-plan-v1`, `fix-report-v1`, `improvement-report-v1`) and all 5 dimension plugins (`correctness`, `architecture`, `performance`, `security`, `maintainability`).
- **[Proposal 4 — STRUCTURAL][LOW]** Removed "internally:" parentheticals from fan-out cardinality sections in N11-aggregator, N16-fix-triage, and N26-oef. Graph topology edges now document only the graph-level cardinality; internal transform ratios are implementation detail.
- **[Proposal 5 — ENHANCEMENT][MEDIUM]** SKILL.md §19 version reference synced: `graph.json is at version 2.0.3` (was `2.0.2`). Pipeline diagram title updated to v2.0.3.
- **[Proposal 6 — ENHANCEMENT][LOW]** Documented `--improve --fix` combined behavior: new row in mode interaction table (§2), new path in pipeline diagram (§4). Combined form runs both pipelines sequentially on one audit report.
- **[Proposal 7 — ENHANCEMENT][LOW]** CHANGELOG.md v2.0.3 section extended with this self-audit-improver pass entry.

## [2.0.2] — 2026-04-29

Third-pass adversarial-audit remediation. Closes 17 findings (4 CRITICAL, 7 HIGH, 4 MEDIUM, 2 LOW). Total test count: 151 → 175.

### Fixed (CRITICAL)

- **F101 + F102** — Three new graph edges (`E_trace_detector`, `E_trace_section`, `E_log_thread`) wire N14's documented inputs (`detector_confidence_trace`, `section_selector_confidence`, `falsifiability_survival_log`) directly to their producers. The "passed through N13" claim was empty — N11/N12/N13 never carried the payloads.
- **F103** — `additionalProperties: false` actually applied to `audit-report-v1.schema.json` top level. The v2.0.1 contract claim that the wrapper form was rejected is now empirically true.
- **F104** — N14 halt-on-q-gate-failure two-axis-below-threshold subreason now uses explicit parentheses: `(creativity < 7 OR functional_correctness < 7) AND (user did not override)`. Fixes the v2.0.1 ambiguous OR-AND precedence that silently ignored override on creativity-only failure.

### Fixed (HIGH)

- **F105** — Two-axis rubric replaced with mechanical predicate tables. Each axis sums points across deterministic predicates over the validated_report's frontmatter and finding bodies. Two implementations evaluating the same report MUST produce identical scores.
- **F106** — N20 outputs `failure_class` enum extended to include the 4 v2.0.1 additions (`markdown-lint-failure`, `cross-reference-failure`, `schema-validation-failure`, `dependency-cycle-failure`) plus new v2.0.2 `tool-unavailable`.
- **F107** — N16 suspicious-content detector adds a SECURITY allow-list: findings with `dimensions` containing `SECURITY` AND a valid built-in `provenance.node` are exempt from rule 1 (prompt-injection trigger phrases). Findings without trusted provenance still get the full check.
- **F108** — N16 multi-file fix-group merging now bounded: `max-merged-files-per-group: 10`, `max-merge-depth: 3`. CLI flags `--max-fix-group-size` and `--max-merge-depth` allow override. Cap-hit splits into multiple groups with `defer_reason: "fix-group-size-cap"`.
- **F109** — graph.json conventions now use normative MUST language and have programmatic enforcement tests in `tests/integration/test_v2_0_2_fixes.py` (was: documented but unenforced).
- **F110** — audit-report-v1 schema Finding ID regex extended to `^F(new[0-9]{3,}|[0-9]{3,})$` to accept N21-allocated `Fnew0NN` IDs from audit-rerun new findings.
- **F111** — Version strings synchronized: SKILL.md, graph.json, README.md, CHANGELOG all at v2.0.2. Test enforces consistency.

### Fixed (MEDIUM)

- **F112** — SKILL.md §20 back-compat invariants 7 and 11 explicitly call out v2.0.x changes that fire on code paths (recovery-conflict, two-axis gate, frontmatter-trace coherence, suspicious-content scan).
- **F113** — SKILL.md §4 pipeline diagram rewritten for v2.0.2: lists all 9 Pass A checks with halt subreasons, attributes two-axis to N14 (not N15), uses severity-based language for falsifiability scope, shows the new side-channel edges (E_trace_detector / E_trace_section / E_log_thread).
- **F114** — N17 `user_approvals` output shape is per-input-type union (`TieredApprovals` for code, `NonCodeApprovals` with low_risk/high_risk_per_fix for non-code). Discriminator: `input_type` from `triage_result`.
- **F115** — N20 documents tool-availability semantics for every per-type verification step. Default is FAIL-on-missing-tool (not silent PASS); `--skip-verification-tool=<name>` flag for override; N18 PreFlight should detect missing required tools at baseline-capture.

### Fixed (LOW)

- **F116** — N15 prose count corrected from "five" to "six" top-level fields (off-by-one fix).
- **F117** — N26 OEF rule 3 (speculative language) tightened: discard only if the speculative term appears AND prose lacks any quantitative/evidentiary anchor (digit + unit, profiler/measurement marker, or quantified comparison). Reduces false positives on legitimate hedge.

### Changed

- graph.json: version bumped to 2.0.2; 3 new edges added (40 total); N00b/N02/N10 fan-out cardinality updated to reflect side-channel edges
- N10/N14 outputs/inputs: `falsifiability_survival_log` flow now via direct E_log_thread (not threaded through N11/N12/N13)
- N14 contract: 9 Pass A checks with mechanical two-axis rubric; halt-condition explicit parentheses
- N16 contract: suspicious-content SECURITY allow-list; multi-file group caps with split-and-defer
- N17 contract: per-input-type user_approvals union shape
- N20 contract: failure_class enum complete; tool-availability semantics + new failure class
- N26 contract: OEF rule 3 tightened with evidentiary-anchor requirement
- audit-report-v1 schema: `additionalProperties: false`; Finding ID regex accepts `Fnew0NN`

## [2.0.1] — 2026-04-29

Adversarial-audit remediation pass. Closes 22 findings (5 CRITICAL, 8 HIGH, 6 MEDIUM, 3 LOW) from the strategic audit.

### Fixed (CRITICAL)

- **F001** — N02 dimension plugin paths corrected from v1 (`~/.claude/skills/epiphany-audit/dimensions/`) to v2 (`<skill_dir>/dimensions/`); added `plugin_path_resolution` convention to graph.json.
- **F002** — Two-axis hard gate now ENFORCED at N14 Pass A check #8 with `halt-on-q-gate-failure` subreason `two-axis-below-threshold`. SKILL.md §18 rewritten to describe the halt path.
- **F003** — Producers added for the three previously-orphaned schema fields: `tetrad_completeness` (N14 Pass A check #2), `two_axis_scores` (N14 Pass A check #8), `falsifiability_survival_log` (N10 aggregation).
- **F004** — Falsifiability check criterion changed from "creative/novel tag" (no producer) to severity ≥ MEDIUM (objective, present on every finding). Matches the canonical fixture's practice.
- **F005** — N15 outputs flattened to top-level fields (no more `self_audit_traces` wrapper); audit-report.md.template updated to render them in frontmatter.

### Fixed (HIGH)

- **F006** — N20 PerFixVerifier extended with per-input-type verification (markdown lint, cross-reference resolution, schema validation, dependency-cycle detection).
- **F007** — N16 fix-group construction now per-input-type; skill type uses semantic-link merging so SKILL.md + correlated module/schema files form a single multi-file fix-group.
- **F008** — `halt-on-recovery-conflict` is now a declared N16 halt condition with explicit detection logic at fix-mode entry.
- **F009** — graph.schema.json now requires `source` and `target` on every edge (with type `oneOf string|array`) and constrains `channel` to a known enum.
- **F010** — Removed `input_type` from N01.outputs in graph.json (it is set by N00b via E00d feedback); added `input_type_propagation` convention.
- **F011** — Falsifiability counter-argument generation moved from N13 to N10 (which has source-file Read access for stronger rebuttals); N13 only renders.
- **F012** — audit-report.md.template renders `tetrad_completeness`, `two_axis_scores`, `two_axis_scores_overridden_by_user`, and `falsifiability_survival_log` in frontmatter.
- **F013** — `test_v1_minimal_report_validates` fixture flattened to top-level (matched canonical schema); added positive guard test `test_self_audit_fields_at_top_level_canonical`.

### Fixed (MEDIUM)

- **F014** — N02 has an explicit "Activation Resolution Order" section (floor → plugin scope → matrix → multi-type union).
- **F015** — Spawn cap moved to graph.json `conventions.spawn_cap`; N04..N09 module mode lines now reference the shared declaration.
- **F016** — Suspicious-content detector defined in N16 (regex triggers, unicode checks, length cap, shell-meta patterns); auto-discovery hardened with mtime check; commit-message rationale/remediation truncation rule.
- **F017** — Q-GATE Pass A check #9 (frontmatter-trace coherence): N14 inputs now include `detector_confidence_trace` and `section_selector_confidence` to verify dimensions_activated and input_type match the traces.
- **F018** — Added `tests/integration/` with 19 new tests across two files: producer-traceability and hard-gate enforcement. Total test count: 131 → 151.
- **F019** — Documented E00e (N00b → N02) as a clarity/confirmation channel; redundancy preserved for graph readability.

### Fixed (LOW)

- **F020** — Per-type predicate fields declared in N01's project_model: `subsystem_count`, `inter_component_contracts`, `cross_phase_dependency_count`, `references_subagent_orchestration`, `has_token_budgets`, `has_latency_constraints`, `defines_auth`, `defines_data_handling`, `defines_user_input_boundaries`.
- **F021** — Run-log structure (JSONL schema) defined in N13 for tournament-discard auditability.
- **F022** — Optional `plan_metadata` object added to audit-report-v1 schema for plan-document input type structured metadata.

### Changed

- N14 Q-GATE inputs: added detector_confidence_trace, section_selector_confidence, falsifiability_survival_log
- N14 Q-GATE outputs: added tetrad_completeness, two_axis_scores, two_axis_scores_overridden_by_user
- N10 FPV: now generates falsifiability counter-arguments (was N13's job in v2.0.0); aggregates falsifiability_survival_log
- N15 SaveHandler: outputs flattened to top-level enumeration matching the schema
- N20 PerFixVerifier: per-input-type verification logic; new failure classes
- N16 FixTriage: per-input-type fix-group construction with semantic-link merging for skill type
- N02 R-ROUTE: explicit activation resolution order; v2-relative path documentation

## [2.0.0] — 2026-04-29

### Added
- Multi-input-type support: code, specification-document, plan-document, skill, prompt, ambiguous-text (5+1 types)
- N00a AuditabilityPrerequisiteGate — structural surface checks before audit
- N00b InputTypeDetector — fingerprint-based input type detection with confidence thresholds
- Medical-diagnostic finding tetrad on every finding: presenting_symptom, underlying_cause, prognosis, confidence_interval
- Section-activation matrix with per-type ACTIVATE/SUPPRESS/CONDITIONAL rules
- Per-type finding-class suppression rules (13 classes across 5 types)
- Per-type B-FIND gap dimension taxonomy (spec, plan, skill, prompt)
- `--audit --fix` sequential mode (no longer a flag conflict)
- `--fix` no-arg auto-discovery of most recent audit report
- Audit-report prerequisite check at `--fix`/`--improve` entry (recent/stale via `project_content_sha256`)
- Per-input-type confirmation thresholds for non-code fix application
- Multi-file transactional semantics (atomic commit/rollback per fix-group)
- `project_content_sha256` stale-report detection
- Per-type `--deep` semantics (cross-reference, cycle detection, module fan-out, prompt-graph traversal)
- Dimension plugin `applies_to.input_types` extension
- Falsifiability-first creativity check (survived/downgraded/dropped)
- Multi-trial creativity tournament (3 alternative framings, top-ranked emitted)
- Two-axis scoring self-critique (creativity ≥7, functional-correctness ≥7)
- Per-type report slug resolution and hashing scope
- Self-audit trace emission (detector-confidence, section-selector-confidence, tetrad-completeness, falsifiability survival log)
- Detector confidence trace schema and section-selector confidence trace schema
- 4 non-code determinism fixtures (plan-doc-small, prompt-small, skill-small, spec-doc-small) for multi-input-type coverage

### Changed
- SKILL.md: complete rewrite for v2.0.0 multi-input-type scope (790 lines)
- graph.json: version 2.0.0, 29 nodes, 37 edges (5 new data-flow edges: E00a–E00e; plus expanded E13 chain, E15, E16–E21 for improve subpipeline; E_repair, E_rerun_fail, E_diffscope, E_finalize, E_complete, E_halt_partial carried forward from v1.x)
- N01 ContextIntake: extended project_model with type-specific fields for all 5 types
- N02 R-ROUTE: consumes input_type, applies section-activation matrix and finding-class suppression
- N03 B-FIND: per-type gap dimension heuristics
- N13 Formatter: emits medical-diagnostic tetrad, falsifiability check, creativity tournament
- N14 Q-GATE: Pass A tetrad-completeness check
- N15 SaveHandler: self-audit traces, per-type slug resolution, project_content_sha256 computation
- N16 FixTriage: audit-report prerequisite check with stale detection
- N17 FixPlanner: per-input-type confirmation thresholds
- N19 FixApplier: multi-file transactional semantics
- audit-report-v1.schema.json: v2.x extensions (input_type, project_content_sha256, tetrad, falsifiability, detector_confidence, section_selector_confidence)
- dimension-plugin-v1.schema.json: optional applies_to.input_types
- Audit report template: v2.x frontmatter and finding field extensions

### Fixed
- (none — v2.0.0 is additive; all v1.x bugfixes carried forward)

## [1.0.1] — 2026-04-29

### Fixed
- `check_overlap.py`: dimension parsing now strips quotes (bare YAML / JSON / Python repr)
- `check_overlap.py`: location prefix now strips `source/` before matching
- `check_overlap.py`: SKILL path uses `__file__`-relative resolution, not `os.path.expanduser`
- `tests/conftest.py`: removed unused SKILL constant
- `check_module_structure.py`: SKILL path uses `__file__`-relative resolution
- `check_module_structure.py`: regex now uses `re.MULTILINE` for correct section matching
- `test_improvement_report_schema.py`: renamed duplicate test function
- `test_harness_parse.py`: removed unreachable `__wrapped__` branch and unused `types` import
- `test_harness_parse.py`: removed dead `sys.path.insert`, `import tempfile`, and `_write_tmp`

### Added
- `tests/test_harness_parse.py`: guards determinism harness format assumptions (F006 coupling)

## [1.0.0] — 2026-04-27

### Added
- Initial release: 27-node graph-of-thought audit + fix + improve pipeline
- Audit pipeline (N01–N15): ContextIntake, R-ROUTE, B-FIND, five dimension
  analyzers (N04–N08), extensible plugin slot (N09), FPV, Aggregator,
  Prioritizer, Formatter, Q-GATE (Pass A + Pass B), SaveHandler
- Fix pipeline (N16–N23): FixTriage (F-VAL ingest + resume-handler),
  FixPlanner, PreFlight, FixApplier (atomic loop), PerFixVerifier,
  RegressionBattery (battery + tiered audit-rerun), RollbackHandler,
  FixReporter
- Improvement subpipeline (N24–N27): ImprovementContextualizer,
  ImprovementBrainstormer (two-phase), OverEngineeringFilter, ImprovementReporter
- Five JSON schemas: audit-report-v1, fix-report-v1, dry-run-plan-v1,
  dimension-plugin-v1, improvement-report-v1
- Five built-in dimension plugins: correctness, architecture, performance,
  security, maintainability
- Four report templates
- Recovery manifest with boundary-aligned writes and archive lifecycle
- Idempotency state file (state file authoritative; git-log fallback)
- 28 halt states with structured envelopes
- Tests: schema-validation (pytest/jsonschema), smoke scenarios, determinism fixture
