# Changelog

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
