---
schema_version: 2
name: performance
display_name: Performance
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
  input_types: [code, skill]
activation_triggers:
  - type: import_grep
    pattern: "for |while |\\.sort|\\.map|\\.filter|O\\("
    min_matches: 3
exclusions:
  - type: project_size
    max_files: 3
prompt_template: |
  Analyze the target for performance issues. The input_type is {{input_type}}.
  Adapt analysis to the input kind:
  - Code: hot allocations, algorithmic complexity blowups (O(n^2) or worse where
    O(n log n) is available), cache-hostile data structures, false sharing,
    unnecessary repeated work inside loops.
  - Skill: token-budget overruns, subagent dispatch latency, module loading overhead,
    prompt-template size affecting cache-hit rate.
  - Other types: structural inefficiencies (redundant passes, oversized sections,
    unnecessary cross-references that slow comprehension or tooling).
  Only report issues with a concrete, measurable performance impact.
  Tag speculative findings (no profiling evidence) with confidence: LOW.
  For each finding, verify the file:line via Read before reporting.
  Return findings conforming to Audit Report Schema v2.
kb_route_query: null
intra_node_token_budget: 30000
priority: medium
---

# Performance Dimension

Finds hot allocations, complexity blowups, cache-hostile layouts, and false sharing.
Only surface findings with concrete performance impact — speculative ones must be
tagged LOW confidence with a `verify_by` profiling recommendation.
