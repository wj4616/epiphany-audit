# N01 — ContextIntake

**Type:** ingest
**Mode:** inline
**Active in:** `audit` (skipped entirely in `--fix` mode; N01..N15 all skipped when `--fix` is passed directly)

## Inputs

- CLI arguments: `path`, flags (`--audit`, `--verbose`, `--deep`, `--improve`, `--auto`, `--confirm-all`, `--dry-run`, `--escalate-finding F00N`, `--test-cmd '<cmd>'`, `--monorepo-subtree-limit N`, `--full-rerun`, `--no-rerun`, `--reverify-state`)
- Environment: `cwd`, `$HOME`, git state at cwd

## Outputs

```
project_model: {
  audit_target: string,           // resolved absolute path
  language_summary: { [lang]: integer },
  file_count: integer,
  total_lines: integer,
  build_manifest: string | null,
  test_command: string | null,
  git_state: {
    head: string, dirty: boolean, branch: string | null,
    detached: boolean, has_commits: boolean
  },
  entry_points: string[],
  project_type: string[],
  is_monorepo: boolean,
  subtrees: SubtreeDescriptor[]
}
resolved_flags: {
  mode: "audit" | "no-flag",
  verbosity: "verbose" | "normal",
  depth: "deep" | "normal",
  improve: boolean,
  autonomy: "auto" | "confirm-all" | "dry-run" | "default",
  escalated_findings: string[],
  test_cmd_override: string | null,
  monorepo_subtree_limit: integer,
  rerun_override: "full" | "no" | null
}
```

## Side Effects

None. Read-only file-system inspection.

## Halt Conditions

- `halt-pre-audit`: resolution chain exhausted with no target
- `halt-suspicious-target` (hard): resolved root is `$HOME`, `/`, `/etc`, `/usr`, `/var`, `/tmp`, or has >5 top-level project-shaped subdirs
- `halt-ambiguous-target`: nested git repos; session touched multiple projects; polyglot inconclusive
- `halt-on-flag-conflict`: both `--audit` and `--fix`; or both `--dry-run`/`--confirm-all`/`--auto` (>1 set); or both `--full-rerun` and `--no-rerun`
- `halt-on-flag-rejection`: unsupported flag (e.g., `--demote-finding`)
- `halt-on-target-conflict`: both explicit `<path>` and `--fix <report>` given; `realpath(<path>) != realpath(audit_target)`
- `halt-no-source-detected`: binary-only, empty, or documentation-only repo

Warn-and-prompt (soft halt; user may override via `~/.config/epiphany-audit/allowed-roots.json`):
- Resolved root inside `~/.claude/skills/<x>/`, `~/dotfiles`, `~/.config`, `~/Desktop`, `~/Downloads`

## Implied-Context Resolution (deterministic, no silent guessing)

1. Explicit `<path>` argument wins
2. `--fix <report>` → derives target from `audit_target` field after report resolution
3. `cwd` inside git repo → `git rev-parse --show-toplevel`
4. `cwd` itself
5. `halt-pre-audit`

Suspicious-target gate runs on resolved target regardless of resolution path.

## Token Budget

Minimal. Directory listing + git status + build-manifest read. No analysis.

## Backtrack / Aggregation

None. Sole producer of `project_model` and `resolved_flags` — feeds N02..N15.

## Fan-out Cardinality

1:1 → N02 via E01.

## Back-edge Endpoints

None. No incoming back-edges.
