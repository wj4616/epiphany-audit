---
schema_version: 2
name: maintainability
display_name: Maintainability
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
  input_types: [code, specification-document, plan-document, skill, prompt, ambiguous-text]
activation_triggers:
  - type: file_present
    path: "**/*"
exclusions: []
prompt_template: |
  Analyze the target for maintainability issues. The input_type is {{input_type}}.
  Adapt analysis to the input kind:
  - Code: dead code, misleading names, stale comments/TODOs, test coverage gaps,
    excessive function complexity, magic numbers/strings without named constants.
  - Specification-document / Plan-document: broken cross-references, missing
    section ordering, inconsistent terminology, undocumented conventions,
    stale version references, headings without body content.
  - Skill: broken cross-references between SKILL.md and modules, inconsistent
    terminology across artifacts, undocumented conventions, stale version
    references, module files missing from graph.json.
  - Prompt: broken tag references, inconsistent output-format declarations,
    undocumented implicit behavior assumptions.
  For each finding, verify the file:line via Read before reporting.
  Return findings conforming to Audit Report Schema v2.
kb_route_query: null
intra_node_token_budget: 30000
priority: high
---

# Maintainability Dimension

**Floor dimension — always activated regardless of project type.**

Finds code that is technically correct but will become a defect source as the
codebase evolves: dead code, misleading names, stale TODOs, coverage gaps on
failure branches.
