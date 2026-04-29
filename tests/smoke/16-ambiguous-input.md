# Smoke Test 16 — Ambiguous-Text Input (Universal-Only)

**Scenario:** Run `/epiphany-audit --audit` targeting prose text that doesn't match any
specific structural fingerprint strongly enough. Input type classified as `ambiguous-text`.

**Setup:**
- Target is a `.md` or `.txt` file containing freeform prose (a design essay, notes, brainstorming output) with no clear specification/plan/prompt/skill/code structure
- File is git-tracked

**Actions:**
1. Invoke `/epiphany-audit --audit <path-to-prose.md>`
2. Allow N00a/N00b to detect — primary score falls below 0.6 or margin <0.2, triggering `ambiguous-text` fallback
3. Allow audit pipeline (N01–N14) to complete
4. Respond "y" to save prompt (N15)

**Expected outcomes:**
- N00b emits `classified_type: ambiguous-text`, `confidence: ambiguous`
- `detector_confidence.ambiguous_reason` is populated
- N02 section-activation matrix: only CORRECTNESS + MAINTAINABILITY ACTIVATE; all others SUPPRESS
- N03 B-FIND: universal gap dimensions only (no type-specific taxonomy)
- Broadest finding-class suppression set (≥7 classes suppressed including architectural-smell, performance-regression)
- Only universal-dimension findings emitted (no type-specific heuristics applied)
- Every finding has the medical-diagnostic tetrad
- Audit report frontmatter: `input_type: ambiguous-text`
- `--deep` degrades gracefully: universal dimensions run deeper cross-reference but no type-specific deep paths activate
- `--improve` still functional: ImprovementBrainstormer generates universal candidates only
