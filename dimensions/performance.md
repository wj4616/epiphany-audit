---
schema_version: 1
name: performance
display_name: Performance
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
activation_triggers:
  - type: import_grep
    pattern: "for |while |\\.sort|\\.map|\\.filter|O\\("
    min_matches: 3
exclusions:
  - type: project_size
    max_files: 3
prompt_template: |
  Analyze the following code for performance issues. Look for:
  - Hot allocations: objects created on every iteration of a tight loop
  - Algorithmic complexity blowups: O(n^2) or worse where O(n log n) is available
  - Cache layout: data structures that thrash CPU cache (linked lists in hot paths)
  - False sharing: adjacent mutable fields accessed from different threads
  - Unnecessary repeated work: recomputing the same value inside a loop
  Only report issues with a concrete, measurable performance impact.
  Tag speculative findings (no profiling evidence) with confidence: LOW.
  For each finding, verify the file:line via Read before reporting.
  Return findings conforming to Audit Report Schema v1.
kb_route_query: null
intra_node_token_budget: 30000
priority: medium
---

# Performance Dimension

Finds hot allocations, complexity blowups, cache-hostile layouts, and false sharing.
Only surface findings with concrete performance impact — speculative ones must be
tagged LOW confidence with a `verify_by` profiling recommendation.
