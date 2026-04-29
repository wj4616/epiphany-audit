---
schema_version: 1
name: architecture
display_name: Architecture
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
activation_triggers:
  - type: file_present
    path: "**/*"
exclusions:
  - type: project_size
    max_files: 5
prompt_template: |
  Analyze the following code for architectural issues. Look for:
  - Excessive coupling: modules that directly access internals of other modules
  - Circular dependencies: A imports B imports A (or through a chain)
  - God objects: classes/modules with more than 10 distinct responsibilities
  - Duplicated logic: the same non-trivial algorithm implemented in 2+ places
  - Invariant gaps: class invariants that callers can violate without error
  - Latent issues: architectural decisions that are safe now but will break under
    specific future conditions (tag these findings with reachable=false and note
    the reachability condition).
  For each finding, verify the file:line via Read before reporting.
  Return findings conforming to Audit Report Schema v1.
kb_route_query: null
intra_node_token_budget: 30000
priority: medium
---

# Architecture Dimension

Finds structural defects: coupling violations, circular dependencies, god objects,
duplicated logic, and invariant gaps. Tags latent findings with reachability conditions.
