# Smoke Test 18 — Multi-Type Input (Spec with Embedded Code Blocks)

**Scenario:** Run `/epiphany-audit --audit` targeting a specification document that contains
substantial embedded code blocks. Input type detector must classify the dominant type
while recording secondary types; section selector applies the union of activation rules.

**Setup:**
- Target is a `.md` file that is primarily a specification document but contains ≥3 substantial fenced code blocks (Python, each ≥10 lines)
- File is git-tracked

**Actions:**
1. Invoke `/epiphany-audit --audit <path-to-hybrid-spec.md>`
2. Allow N00a/N00b to fingerprint — expect primary `specification-document` with `code` as secondary
3. Allow audit pipeline (N01–N14) to complete
4. Respond "y" to save prompt (N15)

**Expected outcomes:**
- N00b reports `classified_type: specification-document` as primary
- `detector_confidence.multi_type: true` and `secondary_types` includes `code`
- `contained_artifacts` lists each code block with line_range and depth
- `contained_types` includes both `specification-document` and `code`
- N02 section-selector applies union semantics: dimensions CONDITIONAL for code remain CONDITIONAL for the union (CONDITIONAL ∪ SUPPRESS = CONDITIONAL)
- Finding-class suppression: uses specification-document rules (primary type) for the spec prose; may use code rules for findings within embedded code blocks
- Every finding has the medical-diagnostic tetrad
- Report frontmatter: `input_type: specification-document`, `contained_types: [specification-document, code]`
- `section_selector_confidence.multi_type_union` documents the union resolution
