---
schema_version: 2
name: architecture
display_name: Architecture
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
  input_types: [code, specification-document, plan-document, skill]
activation_triggers:
  - type: file_present
    path: "**/*"
exclusions:
  - type: project_size
    max_files: 5
prompt_template: |
  Analyze the target for architectural issues. The input_type is {{input_type}}.
  Adapt analysis to the input kind:
  - Code: excessive coupling, circular dependencies, god objects, duplicated
    logic, invariant gaps, latent issues (tag with reachable=false and note
    the reachability condition).
  - Specification-document: cross-subsystem contract gaps, undefined interfaces
    between components, missing dependency declarations between requirements.
  - Plan-document: cross-phase dependency gaps, missing rollback procedures,
    phase-ordering issues, checkpoint granularity problems.
  - Skill: cross-artifact consistency gaps between SKILL.md and modules,
    topology drift between graph.json and module contracts, undefined module
    interfaces, missing dependency declarations in fan-out sections.
  - Prompt: tag topology inconsistencies, missing meta-source attribution,
    schema-to-output-format mismatches.
  For each finding, verify the file:line via Read before reporting.
  Return findings conforming to Audit Report Schema v2.
kb_route_query: null
intra_node_token_budget: 30000
priority: medium
---

# Architecture Dimension

Finds structural defects: coupling violations, circular dependencies, god objects,
duplicated logic, and invariant gaps. Tags latent findings with reachability conditions.
