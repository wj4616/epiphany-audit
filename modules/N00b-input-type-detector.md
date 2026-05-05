# N00b — InputTypeDetector

**Type:** classifier
**Mode:** inline
**Active in:** `audit`

## Inputs

```
project_model: (from N01)
prerequisite_gate_result: (from N00a, guaranteed "PASS" by E00b activation)
```

## Outputs

```
input_type: string            # one of the 5 named types, or "ambiguous-text"
detector_confidence_trace: {
  classified_type: string,
  confidence: "high" | "marginal" | "ambiguous",
  primary_score: number,
  runner_up_type: string | null,
  runner_up_score: number,
  fingerprints_observed: {
    fingerprint: string,
    matched: boolean,
    weight: number,
    negative?: boolean
  }[],
  multi_type: boolean,
  secondary_types: string[],
  ambiguous_reason: string | null
}
contained_artifacts: {
  type: string,
  line_range: [number, number],
  depth: number
}[]
```

## Side Effects

- Sets `input_type` on N01's `project_model` via feedback edge E00d
- Populates `contained_types` and `contained_artifacts` on `project_model`

No file writes. No LLM calls. Pure structural fingerprinting.

## Halt Conditions

None. The detector always produces a classification — if no type exceeds threshold, it emits `ambiguous-text` rather than halting.

## Fingerprint Matching Algorithm

### Step 1 — Compute per-type fingerprint match scores

For each of the 5 named types, compute a **fingerprint match score** (0.0–1.0):

```
score = (matched_primary / total_primary) - (matched_negative / total_negative)
```

Primary fingerprints push score up; negative fingerprints push it down. A type with zero negative fingerprints in the input gets no penalty.

### Step 2 — Classification heuristics table

| Input Type | Primary Fingerprints | Negative Fingerprints |
|-----------|---------------------|----------------------|
| **code** | Source file extensions (.py,.js,.ts,.cpp,.h,.c,.rs,.go), function/class/keyword declarations, import/include statements, high code-block density (>60% of lines) | Prose-dominant markdown (>70% prose), REQUIREMENT blocks, SKILL.md file present |
| **specification-document** | Hierarchical markdown headings, "REQUIREMENT"/"Acceptance Criteria" blocks, prose-dominant (>70% prose), low code-block density (<20% of lines) | Source file extensions, executable shebang, build config syntax (CMakeLists.txt, Makefile) |
| **plan-document** | Phased structure markers ("Phase 1", "Phase 2", /Phase \\d+/i), checkpoint markers, ordered task lists (`- [ ]` checkboxes), dependency callouts ("depends on", "→") | Inline executable code, language-specific syntax keywords at high density |
| **skill** | SKILL.md file present, YAML frontmatter with `name:` AND (`description:` OR `triggers:`), prose instructions with structural conventions (markdown headings + code fences) | Pure code with no SKILL.md |
| **prompt** | XML-like tagging (`<role>`, `<task>`, `<context>`, `<constraints>`, `<output_format>`, `<verification>`, `<edge_cases>`), `<meta source="..."/>` element, prompt-graph topology references, structured-output schema definitions | Bare source code, plan-phase structure, SKILL.md frontmatter |

### Step 3 — Primary classification

The type with the **highest score** is the primary classification.

## Confidence Threshold

Classification is **confident** (`"high"`) when BOTH:
1. `primary_score >= 0.6`
2. `primary_score - runner_up_score >= 0.2` (margin requirement prevents near-ties)

Classification is **marginal** (`"marginal"`) when:
- `primary_score >= 0.6` BUT `primary_score - runner_up_score < 0.2`

Classification is **ambiguous** (`"ambiguous"`) when:
- `primary_score < 0.6`

## Ambiguous-Text Handling

When confidence is `"ambiguous"`:
- Emit `input_type: "ambiguous-text"`
- Record all 5 type scores in `detector_confidence_trace`
- Set `ambiguous_reason` to describe the shortfall (e.g., "primary score 0.45 below 0.6 threshold; closest type is specification-document")
- Route to N02 with universal-only dimensions (CORRECTNESS + MAINTAINABILITY floor only)

## Multi-Type Classification

When 2+ types exceed a **0.4 confidence floor**:

1. `multi_type: true` in trace
2. `secondary_types` lists all types above 0.4 (excluding primary)
3. UNION semantics apply downstream (see N02 R-ROUTE): a dimension activates if ANY detected type says ACTIVATE
4. SUPPRESSION-OVERRIDE: a finding class is emitted only if NOT marked S for the PRIMARY type
5. Primary tie-breaking (equal scores, both above 0.6): the type with more ACTIVATE cells in the section-activation matrix wins. Tie-breaking rationale recorded in trace.

## Nested / Contained Input Handling

When a top-level artifact contains sub-artifacts (e.g., spec doc with embedded code blocks):

1. Top-level classification drives primary pipeline routing
2. Contained sub-artifacts classified independently → `project_model.contained_types[]`
3. Dimensions suppressed at top level but activated for contained type → activate for contained scope only
4. Recursive containment max depth: **2**; deeper → folded into nearest classified ancestor
5. All nesting recorded in `project_model.contained_artifacts[]` with `{type, line_range, depth}`

## Detector Confidence Trace Emission

Every run emits the full `detector_confidence_trace` — transmitted to N15 SaveHandler for inclusion in the self-audit trace section of the report. The trace is the authoritative record of *why* the pipeline routed the way it did.

**TRACE (mandatory, non-blocking) — immediately after completing classification and before routing forward, call this Bash command.** This is the session-start Langfuse trace for this pipeline run. Substitute: `MODE` = active pipeline mode word (e.g. `audit`, `audit-deep`, `fix`, `improve`); `ITYPE` = classified input_type (e.g. `code`, `specification-document`, `plan-document`, `skill`, `prompt`, or `ambiguous-text`); `TARGET` = first ~150 chars of `project_model.audit_target` collapsed to one line (newlines → spaces, internal `"` escaped as `\"`):
```
python3 ~/.claude/skills/epiphany-audit-v2/scripts/langfuse_tracer.py init --mode "MODE" --input-type "ITYPE" --target "TARGET" 2>/dev/null || true
```

## Token Budget

O(files) with small constants. Directory listing, YAML frontmatter parse, regex fingerprinting. No LLM calls. Typical cost: < 100ms for a directory of 100 files.

## Backtrack / Aggregation

None. Single-pass classifier.

## Fan-out Cardinality

1:3 (v2.0.2) — feedback edge E00d to N01 (sets `input_type` on project_model), forward edge E00e to N02 (routes with classified type), and forward edge E_trace_detector to N14 (carries `detector_confidence_trace` for Pass A check #9 frontmatter coherence).

## Back-edge Endpoints

E00d — feedback edge to N01. N00b writes `input_type` back to N01's `project_model`. N01 does NOT re-ingest; it enriches the existing model with type-specific fields after receiving the classification.
