# N01 — ContextIntake

**Type:** ingest
**Mode:** inline
**Active in:** `audit` (skipped entirely in `--fix <report>` with explicit report; runs for `--fix` no-arg auto-discover to resolve target)

## Inputs

- CLI arguments: `path`, flags (`--audit`, `--verbose`, `--deep`, `--improve`, `--fix`, `--auto`, `--confirm-all`, `--dry-run`, `--escalate-finding F00N`, `--test-cmd '<cmd>'`, `--monorepo-subtree-limit N`, `--full-rerun`, `--no-rerun`, `--reverify-state`)
- Environment: `cwd`, `$HOME`, git state at cwd

## Outputs

```
project_model: {
  audit_target: string,           // resolved absolute path

  // --- v2.x: set by N00b via feedback edge E00d; null at N01 output ---
  input_type: string | null,

  // --- universal (present for all input types) ---
  file_count: integer,
  total_lines: integer,
  git_state: {
    head: string, dirty: boolean, branch: string | null,
    detached: boolean, has_commits: boolean
  },
  contained_types: string[],
  contained_artifacts: {
    type: string,
    line_range: [number, number],
    depth: number
  }[],

  // --- code-specific (unchanged from v1.x; only populated when input_type == "code") ---
  language_summary: { [lang]: integer },
  build_manifest: string | null,
  test_command: string | null,
  entry_points: string[],
  project_type: string[],
  is_monorepo: boolean,
  subtrees: SubtreeDescriptor[],

  // --- specification-document-specific (when input_type == "specification-document") ---
  heading_hierarchy?: { depth_max: integer, heading_map: { [depth]: integer } },
  requirement_blocks_count?: integer,
  acceptance_criteria_count?: integer,
  has_rationale_sections?: boolean,
  embedded_code_block_count?: integer,
  spec_authoring_skill?: string | null,
  // --- v2.0.1: predicate fields used by SKILL.md §7 conditions (a)/(e) ---
  subsystem_count?: integer,                 // distinct top-level header roots; condition (a)
  inter_component_contracts?: integer,       // count of "interface"/"API"/"contract" mentions
  defines_auth?: boolean,                    // regex match for auth/jwt/session/oauth; condition (e)
  defines_data_handling?: boolean,           // regex match for "data handling"/"data flow"/"PII"
  defines_user_input_boundaries?: boolean,   // regex match for "user input"/"untrusted input"

  // --- plan-document-specific (when input_type == "plan-document") ---
  phase_count?: integer,
  phase_ids?: string[],
  checkpoint_count?: integer,
  dependency_graph?: { [phase_id: string]: string[] },
  task_list_count?: integer,
  has_rollback_procedure?: boolean,
  // --- v2.0.1: predicate field used by SKILL.md §7 condition (b) ---
  cross_phase_dependency_count?: integer,    // total edges in dependency_graph; condition (b)

  // --- skill-specific (when input_type == "skill") ---
  skill_name?: string,
  has_frontmatter?: boolean,
  frontmatter_fields?: string[],
  supporting_file_count?: integer,
  module_count?: integer,
  has_tests?: boolean,
  skill_language_summary?: { [lang]: integer },
  // --- v2.0.1: predicate fields used by SKILL.md §7 conditions (c)/(d) ---
  references_subagent_orchestration?: boolean,  // regex match for "subagent"/"Agent tool"; (c)
  has_token_budgets?: boolean,                   // SKILL.md contains "token budget"; condition (d)
  has_latency_constraints?: boolean,             // SKILL.md contains "latency"/"wall-clock"; (d)

  // --- prompt-specific (when input_type == "prompt") ---
  tag_topology?: { [tag_name: string]: integer },
  meta_source?: string | null,
  has_output_format?: boolean,
  has_verification?: boolean,
  has_edge_cases?: boolean,
  embedded_schema_count?: integer,
  prompt_authoring_skill?: string | null,

  // --- ambiguous-text-specific (when input_type == "ambiguous-text") ---
  observed_fingerprints?: string[],
  detector_confidence?: number,
  all_type_scores?: {
    code: number,
    "specification-document": number,
    "plan-document": number,
    skill: number,
    prompt: number
  }
}
resolved_flags: {
  mode: "audit" | "no-flag" | "fix" | "improve" | "audit-then-fix",
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
- `halt-on-flag-conflict`: `--audit` + `--fix <report>` (explicit report bypasses fresh audit); or both `--dry-run`/`--confirm-all`/`--auto` (>1 set); or both `--full-rerun` and `--no-rerun`

  **v2.x change (F004):** `--audit` + `--fix` (no report arg) is NO LONGER a conflict. Set `resolved_flags.mode` to `"audit-then-fix"` — audit runs first, then fix automatically consumes the resulting report.
- `halt-on-flag-rejection`: unsupported flag (e.g., `--demote-finding`)
- `halt-on-target-conflict`: both explicit `<path>` and `--fix <report>` given; `realpath(<path>) != realpath(audit_target)`
- `halt-no-source-detected`: no text files with >=50 tokens and >=1 structural marker exist in the target. **v2.x change (F005):** "documentation-only" is no longer a halt trigger — documentation IS auditable. A directory of markdown spec/plan/prompt files is a valid audit target.

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

1:2 — feeds N00a via E00a (auditability prerequisite gate, v2.x); also receives feedback from N00b via E00d (input_type enrichment). All downstream nodes consume the enriched project_model from N01.

## Back-edge Endpoints

E00d — incoming feedback edge from N00b InputTypeDetector. N01 receives `input_type`, then enriches the project_model with type-specific fields. This is the ONLY back-edge into N01.
