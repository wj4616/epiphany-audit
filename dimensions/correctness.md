---
schema_version: 1
name: correctness
display_name: Correctness
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
activation_triggers:
  - type: file_present
    path: "**/*"
exclusions: []
prompt_template: |
  Analyze the following code for correctness issues. Look for:
  - Logic errors: off-by-one, wrong conditional, inverted boolean
  - Type/lifetime errors: mismatched types, use-after-free, null dereference
  - Boundary violations: unchecked array access, integer overflow, buffer overrun
  - Concurrency: data races, missing locks, TOCTOU
  - Resource leaks: unclosed files, unreleased memory, leaked handles
  - Error paths: silently swallowed exceptions, ignored return codes
  For each finding, verify the file:line via Read before reporting.
  Return findings conforming to Audit Report Schema v1.
kb_route_query: null
intra_node_token_budget: 30000
priority: high
---

# Correctness Dimension

**Floor dimension — always activated regardless of project type.**

Finds defects where the code produces wrong results, crashes, or corrupts state.
Covers the full CORRECTNESS taxonomy: logic errors, type/lifetime, boundary,
concurrency, resource leaks, and error paths.

## Failure modes (non-exhaustive)

- Loop bounds (off-by-one)
- Null/None dereference on unchecked return values
- Integer wrap/overflow in size calculations
- Race conditions on shared mutable state
- File handles / DB connections not closed on exception path
- Exception caught and silently dropped with `pass` / `catch (Exception e) {}`
- Wrong operator precedence (`a & b == c` instead of `(a & b) == c`)
- Incorrect use of mutable default arguments (Python)
