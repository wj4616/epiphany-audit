# epiphany-audit v2.0.0

Multi-input-type graph-of-thought audit skill for Claude Code. Audits code,
specification documents, plan documents, AI agent skills, and detailed prompts,
then optionally drives a safeguarded fix pipeline with idempotent recovery.

## Supported Input Types

| Type | Description |
|------|-------------|
| Code | Git-tracked projects (C++, Python, JS, etc.) |
| Specification document | Design specs with requirements/acceptance criteria |
| Plan document | Implementation plans with phases/checkpoints/dependencies |
| Skill | Claude Code AI agent skill directories |
| Prompt | Detailed prompts with XML tag structure |
| Ambiguous text | Fallback — universal dimensions only |

Input type is auto-detected via structural fingerprinting at audit time.

## Invocation

~~~
/epiphany-audit [<path>] [--audit | --fix [<report>] | --improve]
                [--verbose] [--deep]
                [--auto | --confirm-all | --dry-run]
                [--escalate-finding F00N] [--test-cmd '<cmd>']
                [--monorepo-subtree-limit N] [--reverify-state]
                [--full-rerun | --no-rerun]
~~~

See `SKILL.md` for the complete invocation contract, node registry,
halt states, and behavioral specification.

## Output locations

- Audit reports: `~/docs/epiphany/audit/`
- Fix reports:   `~/docs/epiphany/audit/fix-reports/`
- Dry-run plans: `~/docs/epiphany/audit/dry-run-plans/`
- Improvements:  `~/docs/epiphany/audit/improvement-reports/`
- State files:   `~/docs/epiphany/audit/.state/`
- Recovery:      `~/docs/epiphany/audit/.recovery/`
- Logs:          `~/docs/epiphany/audit/.logs/`

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
