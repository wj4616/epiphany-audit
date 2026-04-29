# epiphany-audit

Graph-of-thought audit skill for Claude Code. Runs a multidimensional,
project-aware audit on any codebase, then optionally drives a safeguarded
fix pipeline with idempotent recovery.

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

- Audit reports: `~/docs/epiphany/audit/`
- Fix reports:   `~/docs/epiphany/audit/fix-reports/`
- Dry-run plans: `~/docs/epiphany/audit/dry-run-plans/`
- Improvements:  `~/docs/epiphany/audit/improvement-reports/`
- State files:   `~/docs/epiphany/audit/.state/`
- Recovery:      `~/docs/epiphany/audit/.recovery/`
- Logs:          `~/docs/epiphany/audit/.logs/`
