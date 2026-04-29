# Changelog

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
