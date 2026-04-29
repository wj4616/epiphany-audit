---
schema_version: 1
name: test-custom-dim
display_name: Test Custom Dimension
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
activation_triggers:
  - type: file_present
    path: "**/*.py"
exclusions: []
prompt_template: |
  Analyze the following code for test-custom-dim issues.
  Look for any function named `test_custom_target`.
  Return findings conforming to Audit Report Schema v1.
kb_route_query: null
intra_node_token_budget: 5000
priority: low
---

# Test Custom Dimension (smoke test fixture)

Used by smoke test 08 only. Not a real dimension.
