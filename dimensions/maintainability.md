---
schema_version: 1
name: maintainability
display_name: Maintainability
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
activation_triggers:
  - type: file_present
    path: "**/*"
exclusions: []
prompt_template: |
  Analyze the following code for maintainability issues. Look for:
  - Dead code: unreachable branches, unused variables/functions/imports with no callers
  - Misleading names: identifiers whose names contradict their behavior
  - Stale comments/TODOs: TODOs referencing issues that are already closed or resolved
  - Test coverage gaps: failure-mode branches with no corresponding test
  - Excessive complexity: functions >50 lines with no natural split point
  - Magic numbers/strings without named constants
  For each finding, verify the file:line via Read before reporting.
  Return findings conforming to Audit Report Schema v1.
kb_route_query: null
intra_node_token_budget: 30000
priority: high
---

# Maintainability Dimension

**Floor dimension — always activated regardless of project type.**

Finds code that is technically correct but will become a defect source as the
codebase evolves: dead code, misleading names, stale TODOs, coverage gaps on
failure branches.
