# N07 — DimensionAnalyzer.SECURITY

**Type:** analyzer
**Mode:** inline (default); subagent under `--deep` — subject to the **shared spawn cap** declared in `graph.json` `conventions.spawn_cap`: N04..N09 share ONE subagent slot, not one per analyzer.
**Active in:** `audit`

## Inputs

```
project_model: (from N01)
file_subset: string[]
resolved_flags: (from N01)
```

## Outputs

```
raw_findings: Finding[]
```

## Side Effects

Read-only.

## Halt Conditions

None.

## Analysis Scope

Per-surface sub-routing (run only sub-surfaces where the project has the relevant component):

| Sub-surface     | Trigger                                          |
|-----------------|--------------------------------------------------|
| SQL injection   | DB layer detected (psycopg, sqlite3, sqlalchemy) |
| Shell injection | subprocess/exec/os.system usage                  |
| Auth/authz      | auth/jwt/session patterns detected               |
| Secrets in code | grep for `password`, `secret`, `api_key`, `token` literals |
| Deserialization | pickle/eval/yaml.load on untrusted data          |
| Prompt injection| LLM-facing code concatenating user input into prompts |

Skipped sub-surfaces appear in the audit report with reason.

## Token Budget

30k tokens per invocation.

## Backtrack / Aggregation

Participant in BACKTRACKING via N10 (single re-emit cap).

## Fan-out Cardinality

1:1 → N10 via E05 (producing many findings; the fan-in is described by E05's multi-source topology).

## Back-edge Endpoints

E06: N10 → N07.
