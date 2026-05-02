# N02 — RelevanceRouter (R-ROUTE)

**Type:** router
**Mode:** inline
**Active in:** `audit`

## Inputs

```
project_model: (from N01, now includes input_type set by N00b)
dimension_plugins: Plugin[]  // loaded at N02 startup from:
                             // (1) <skill_dir>/dimensions/*.md  (resolves at runtime to
                             //     ~/.claude/skills/epiphany-audit-v2/dimensions/*.md)
                             // (2) ~/.config/epiphany-audit/dimensions/*.md
resolved_flags: (from N01)
input_type: string           // consumed from project_model;
                             // set by N00b InputTypeDetector via E00d → N01
```

## Outputs

```
dimension_activation_map: {
  activated: string[],
  skipped: { dimension: string, reason: string }[]
}
subtrees_activation_maps: SubtreeActivationMap[]  // only for monorepos
plugin_registry: Plugin[]          // validated, ordered
kb_prefetch_results: { [dim]: string }  // for plugins with kb_route_query
file_subset: string[]              // files scoped to activated dimensions;
                                   // derived from dimension_activation_map at end of R-ROUTE
```

## Side Effects

- Read: `<skill_dir>/dimensions/*.md` — at runtime resolves to `~/.claude/skills/epiphany-audit-v2/dimensions/*.md`
- Read: `~/.config/epiphany-audit/dimensions/*.md` (if exists)
- Write-log: one structured event per plugin load attempt (success / validation-fail / shadowed / rejected)

## Halt Conditions

- `halt-on-floor-plugin-missing`: `correctness.md` or `maintainability.md` missing from skill-bundled `dimensions/`. Subreason: `<plugin-name>`. A floor plugin that fails schema validation also triggers this halt.

Logged, not halted:
- Plugin fails schema validation → skip and log
- Two user plugins share same `name` → alphabetical loser logged and skipped
- User plugin shadows CORRECTNESS or MAINTAINABILITY → rejected with warning

## Floor Invariant

CORRECTNESS + MAINTAINABILITY are always activated regardless of input type, plugin presence, or activation triggers. R-ROUTE cannot suppress floor dimensions. This invariant is preserved from v1.x — the floor dimensions are the only dimensions guaranteed active for ALL input types including `ambiguous-text`.

## Section-Activation Matrix (v2.x — per-input-type dimension gating)

After floor activation, the remaining built-in dimensions (ARCHITECTURE, PERFORMANCE, SECURITY) are gated by the input type. Rows = dimensions, Columns = input types. A=ACTIVATE, S=SUPPRESS, C=CONDITIONAL.

```
DIMENSION              | CODE  | SPEC  | PLAN  | SKILL | PROMPT | AMBIGUOUS
-----------------------+-------+-------+-------+-------+--------+----------
CORRECTNESS (floor)    |   A   |   A   |   A   |   A   |   A    |    A
MAINTAINABILITY (floor)|   A   |   A   |   A   |   A   |   A    |    A
ARCHITECTURE           |   A   | C(a)  | C(b)  | C(c)  |   S    |    S
PERFORMANCE            |   A   |   S   |   S   | C(d)  |   S    |    S
SECURITY               |   A   | C(e)  |   S   |   A   |   A    |    C(f)
```

**Condition notes:**
- **(a)** ARCHITECTURE on SPEC: ACTIVATE if spec spans >=3 subsystems or defines inter-component contracts; else SUPPRESS.
- **(b)** ARCHITECTURE on PLAN: ACTIVATE if plan has >=3 phases with cross-phase dependencies; else SUPPRESS.
- **(c)** ARCHITECTURE on SKILL: ACTIVATE if skill directory has >=3 modules or references subagent orchestration; else SUPPRESS.
- **(d)** PERFORMANCE on SKILL: ACTIVATE if SKILL.md specifies token budgets or latency constraints; else SUPPRESS.
- **(e)** SECURITY on SPEC: ACTIVATE if spec defines auth, data handling, or user-input boundaries; else SUPPRESS.
- **(f)** SECURITY on AMBIGUOUS: ACTIVATE only universal-injection-surface checks; SUPPRESS language-specific vulnerability scans.

**Back-compat invariant:** When `input_type == "code"`, the matrix produces identical activation outcomes to v1.x — all 5 dimensions activate unconditionally. The code path through R-ROUTE is unchanged.

## Per-Dimension Finding-Class Suppression Rules (v2.x)

Beyond dimension-level activation, individual finding classes are suppressed per input type. A dimension may be ACTIVE but certain finding classes within it are gated:

```
Finding class                  | CODE | SPEC | PLAN | SKILL | PROMPT
-------------------------------|------|------|------|-------|-------
race-condition / deadlock      |  A   |  S   |  S   | C(g)  |  S
missing-test-coverage          |  A   | C(h) |  S   |  A    |  S
phase-ordering-inconsistency   |  S   | C(i) |  A   | C(i)  |  S
prompt-injection-surface       |  S   | C(j) |  S   |  A    |  A
schema-drift                   |  S   |  A   |  A   |  A    |  A
structural-contradiction       |  S   |  A   |  A   |  A    |  A
missing-rollback-procedure     |  S   |  S   |  A   | C(k)  |  S
undefined-acceptance-criteria  |  S   |  A   |  S   |  S    |  S
technique-application-inconsistency | S |  S   |  S   |  S    |  A
build-config-integrity         |  A   |  S   |  S   |  S    |  S
dependency-cycle               |  A   | C(l) |  A   | C(m)  |  S
kb-route-query-staleness       |  S   |  S   |  S   |  A    |  S
output-format-underspecification| S   |  A   |  A   |  A    |  A
```

**Condition notes:**
- **(g)** SKILL concurrency: only if SKILL.md or modules reference concurrency/threading/async.
- **(h)** SPEC test-coverage: only if spec defines testable acceptance criteria with concrete pass/fail predicates.
- **(i)** phase-ordering on SPEC/SKILL: only if document has explicit sequential/phase structure.
- **(j)** SPEC injection: only if spec defines user-facing input fields or prompt templates.
- **(k)** SKILL rollback: only if skill writes files (has a write-tool footprint).
- **(l)** SPEC dependency-cycle: only if spec defines multi-component dependency graph.
- **(m)** SKILL dependency-cycle: only if skill has >=3 modules with cross-references.

## Section-Selector-Confidence Trace Emission (v2.x)

Every R-ROUTE activation produces a `section_selector_confidence` trace transmitted to N15 SaveHandler for inclusion in the self-audit trace. Example structure:

```yaml
section_selector_confidence:
  input_type: "specification-document"
  dimensions:
    CORRECTNESS:
      status: "ACTIVATED"
      reason: "floor — always on"
    MAINTAINABILITY:
      status: "ACTIVATED"
      reason: "floor — always on"
    ARCHITECTURE:
      status: "SUPPRESSED"
      reason: "spec spans <3 subsystems, no inter-component contracts detected"
    PERFORMANCE:
      status: "SUPPRESSED"
      reason: "non-code input type — PERFORMANCE suppressed for specification-document"
    SECURITY:
      status: "SUPPRESSED"
      reason: "spec does not define auth, data handling, or user-input boundaries"
  finding_class_suppressions:
    - "race-condition/deadlock — suppressed (code-only)"
    - "missing-test-coverage — CONDITIONAL (spec has testable acceptance criteria: no → suppressed)"
  multi_type_union:
    active: false
    primary_type: "specification-document"
    union_types: []
```

## Multi-Type Classification Handling (v2.x)

When the detector reports 2+ types above 0.4 confidence:

1. **UNION rule** — if ANY detected type says A for a dimension → dimension is ACTIVATED.
2. **SUPPRESSION-OVERRIDE** — a finding class is emitted only if NOT marked S for the PRIMARY type (highest-confidence type).
3. CONDITIONAL cells evaluate independently; if condition met for any detected type → dimension activates.
4. DUAL-PRIMARY tie (equal confidence) → primary is the type with more ACTIVATE cells in the matrix. Tie-breaking rationale recorded in trace.
5. All detected types recorded in `section_selector_confidence.multi_type_union`.

## Loading and Shadow Rules

1. Bundled plugins: `<skill_dir>/dimensions/*.md` — at runtime resolves to `~/.claude/skills/epiphany-audit-v2/dimensions/*.md`. Implementations MUST use `<skill_dir>`-relative resolution (e.g., `__file__`-relative in Python harnesses) and MUST NOT hardcode the v1 path `~/.claude/skills/epiphany-audit/`.
2. User plugins: `~/.config/epiphany-audit/dimensions/*.md` (loaded after; may shadow by `name`)
3. User plugin with same `name` as bundled → shadows bundled entirely (no merge)
4. CORRECTNESS and MAINTAINABILITY cannot be shadowed (warning emitted, user plugin rejected)
5. Alphabetical wins between two user plugins sharing a name

## Activation Resolution Order (v2.0.1)

Two activation gates exist: the plugin's `applies_to.input_types` field and the SKILL.md §7 section-activation matrix. They compose by AND-with-conditional-evaluation, in this strict order:

1. **Floor invariant**: CORRECTNESS and MAINTAINABILITY → ACTIVATED for every input type, regardless of plugin or matrix. They cannot be suppressed at any layer.
2. **Plugin-scope gate**: for each non-floor dimension, check `applies_to.input_types` (default `[code]` if absent). If `input_type` is NOT in the plugin's set → SUPPRESSED with reason `"plugin scope (applies_to.input_types) excludes <input_type>"`.
3. **Matrix gate**: if the plugin admits the input type, look up the cell in §7's matrix:
   - `A` → ACTIVATED
   - `S` → SUPPRESSED with reason quoting the matrix cell
   - `C` → evaluate the predicate (a)–(f); ACTIVATED if true, SUPPRESSED if false (with the predicate's failure quoted as reason)
4. **Multi-type union override**: if the detector reported `multi_type: true` (≥2 input types above 0.4 confidence), apply §11's UNION rule — any S → A if any detected type says A for that dimension. SUPPRESSION-OVERRIDE applies to finding classes only (per §8), not to dimension activation.

**Worked example:** input is `skill`, plugin is performance.md (applies_to.input_types: [code, skill]):
- Floor: not floor — proceed.
- Plugin gate: `skill ∈ [code, skill]` → admitted.
- Matrix: PERFORMANCE on SKILL = `C(d)` — evaluate "SKILL.md specifies token budgets or latency constraints". If true → ACTIVATED; if false → SUPPRESSED.

This ordering is deterministic and debuggable. The `section_selector_confidence` trace records the first gate that suppressed each dimension.

## Activation Trigger Logic (per plugin)

ALL `activation_triggers` must match for activation:
- `file_present`: path glob matches any file in project tree
- `import_grep`: pattern grepped, `min_matches` met

ANY `exclusions` match → dimension skipped.

## Token Budget

Low (directory listing + YAML plugin manifest reads). No analysis.

## Backtrack / Aggregation

None. Produces activation map consumed by N03 and N04..N09.

## Fan-out Cardinality

1:2 (v2.0.2) — primary 1:1 → N03 (E02; carries dimension_activation_map for B-FIND), and side-channel 1:1 → N14 (E_trace_section; carries `section_selector_confidence` for Pass A check #9 frontmatter coherence). The 1:N fan-out to N04..N09 happens downstream via N03's E03 edge, which consumes the dimension_activation_map produced here.

## Back-edge Endpoints

None.
