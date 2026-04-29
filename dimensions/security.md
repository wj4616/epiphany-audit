---
schema_version: 1
name: security
display_name: Security
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
activation_triggers:
  - type: import_grep
    pattern: "subprocess|exec|eval|os\\.system|request|sqlite|psycopg|http|jwt|auth|secret|password|token"
    min_matches: 1
exclusions: []
prompt_template: |
  Analyze the following code for security vulnerabilities using sub-surface routing:
  - SQL injection: string-interpolated queries, no parameterization
  - Shell injection: user input passed to subprocess/exec/os.system without sanitization
  - Auth/authz: missing authentication checks, broken access control
  - Secrets in source: hardcoded credentials, API keys, private keys
  - Deserialization: unsafe pickle/eval/yaml.load on untrusted input
  - Prompt injection: LLM-facing code that concatenates user input directly into prompts
  Only activate sub-surfaces where the project has the relevant component.
  Emit skipped sub-surfaces with reason in the report.
  For each finding, verify the file:line via Read before reporting.
  Return findings conforming to Audit Report Schema v1.
kb_route_query: null
intra_node_token_budget: 30000
priority: high
---

# Security Dimension

Per-surface sub-routing for SQL, shell, auth, secrets, deserialization, and
prompt-injection. Only activates sub-surfaces where the project has the relevant
component (e.g., skips SQL sub-surface when no DB layer detected).
