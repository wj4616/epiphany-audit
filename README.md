# epiphany-audit

`epiphany-audit` is a Graph-of-Thought audit skill for Claude Code. It runs a
multidimensional, project-aware audit on any codebase — surfacing findings
across security, performance, correctness, architecture, maintainability, and
more — then optionally drives a safeguarded fix pipeline with per-finding
confirmation and idempotent recovery. Every finding is anchored to a verified
`file:line` location; no hallucinated citations.

## Modes

### Audit mode (`--audit`)

Runs the full multidimensional audit pipeline. The skill probes the codebase
across up to nine configurable dimensions, prunes irrelevant ones via R-ROUTE
(with explicit rationale), and surfaces project-specific blindspots via B-FIND.
Findings are ranked by severity and written to a structured report under
`~/docs/epiphany/audit/`.

Add `--improve` to also generate improvement recommendations (written to
`~/docs/epiphany/audit/improvement-reports/`). Add `--deep` for a deeper
analysis pass on ambiguous findings.

### Fix mode (`--fix <report>`)

Consumes a prior audit report and drives the safeguarded fix pipeline. By
default each fix requires per-tier user confirmation before it is applied.
State is tracked via a recovery manifest so the pipeline can resume safely
after interruption.

Use `--dry-run` to emit the fix plan and diffs without applying anything.
Use `--auto` for silent Tier-1 apply / batch Tier-2 / per-fix Tier-3. Use
`--confirm-all` to require explicit confirmation for every fix regardless of
tier. `--dry-run` takes precedence over `--confirm-all` over `--auto` on
conflict.

## Invocation

~~~
/epiphany-audit [<path>] [--audit | --fix <report>] [--verbose] [--deep]
                [--improve] [--auto | --confirm-all | --dry-run]
                [--escalate-finding F00N] [--test-cmd '<cmd>']
                [--monorepo-subtree-limit N] [--reverify-state]
                [--full-rerun | --no-rerun]
~~~

See `SKILL.md` for the complete invocation contract, node registry,
halt states, and behavioral specification.

## Output locations

| Directory | Contents |
|-----------|----------|
| `~/docs/epiphany/audit/` | Audit reports |
| `~/docs/epiphany/audit/fix-reports/` | Fix pipeline reports |
| `~/docs/epiphany/audit/dry-run-plans/` | Dry-run diff plans |
| `~/docs/epiphany/audit/improvement-reports/` | Improvement recommendations |
| `~/docs/epiphany/audit/.state/` | Fix-pipeline state files |
| `~/docs/epiphany/audit/.recovery/` | Recovery manifests |
| `~/docs/epiphany/audit/.logs/` | Execution logs |

## Development

**Install test dependencies:**

~~~bash
pip install -r tests/requirements.txt
~~~

**Run tests:**

~~~bash
pytest -q
~~~

**Run determinism harness manually:**

~~~bash
python tests/determinism/check_overlap.py <audit-report.md> [--fixture python-small]
~~~

**Install pre-commit hooks (optional):**

~~~bash
pip install pre-commit && pre-commit install
~~~
