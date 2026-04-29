# Changelog

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

### Changed
- SKILL.md: complete rewrite for v2.0.0 multi-input-type scope (790 lines)
- graph.json: version 2.0.0, 29 nodes, 29 edges (5 new: E00a–E00e)
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
