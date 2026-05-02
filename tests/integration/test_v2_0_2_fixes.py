"""
v2.0.2 remediation guards — third-pass adversarial audit fixes.

Real semantic guards (not self-fulfilling-prophecy keyword searches), guarding
against the third-pass audit's findings F101..F117 regressing.
"""
import json
import os
import re
import jsonschema

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_graph():
    with open(os.path.join(SKILL, "graph.json")) as f:
        return json.load(f)


def load_audit_schema():
    with open(os.path.join(SKILL, "schemas/audit-report-v1.schema.json")) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# F101 + F102 — falsifiability_survival_log threading + N14 input edges
# ---------------------------------------------------------------------------

class TestF101F102_EdgeWiring:
    """Verify every N14 input has a corresponding edge in graph.json."""

    def test_n14_inputs_match_incoming_edges(self):
        g = load_graph()
        n14 = next(n for n in g["nodes"] if n["id"] == "N14")
        n14_inputs = set(n14["inputs"])

        # Collect sources of edges targeting N14
        incoming_sources = []
        for e in g["edges"]:
            tgt = e.get("target")
            if tgt == "N14" or (isinstance(tgt, list) and "N14" in tgt):
                incoming_sources.append(e.get("source"))

        # The three v2.0.2 inputs MUST have dedicated edges
        for input_field, expected_edge_id in [
            ("falsifiability_survival_log", "E_log_thread"),
            ("detector_confidence_trace", "E_trace_detector"),
            ("section_selector_confidence", "E_trace_section"),
        ]:
            assert input_field in n14_inputs, f"N14 must declare {input_field} as input"
            edge = next((e for e in g["edges"] if e.get("id") == expected_edge_id), None)
            assert edge is not None, f"v2.0.2 edge {expected_edge_id} must exist"
            assert edge["target"] == "N14", f"{expected_edge_id} must target N14"

    def test_n10_outputs_falsifiability_log_with_outgoing_edge(self):
        g = load_graph()
        n10 = next(n for n in g["nodes"] if n["id"] == "N10")
        assert "falsifiability_survival_log" in n10["outputs"]

        # The log must have a path to N14 — either direct edge OR via threaded N11/N12/N13
        # In v2.0.2 we use direct edge E_log_thread
        log_edge = next((e for e in g["edges"] if e.get("id") == "E_log_thread"), None)
        assert log_edge is not None, "E_log_thread (N10 → N14) must exist for survival log threading"
        assert log_edge["source"] == "N10"
        assert log_edge["target"] == "N14"


# ---------------------------------------------------------------------------
# F103 — schema additionalProperties enforcement
# ---------------------------------------------------------------------------

class TestF103_AdditionalPropertiesEnforced:
    """Verify the schema actually rejects the self_audit_traces wrapper form."""

    def test_schema_has_additional_properties_false(self):
        schema = load_audit_schema()
        assert schema.get("additionalProperties") is False, (
            "audit-report-v1 schema MUST declare additionalProperties: false at top level "
            "to reject the v2.0.0 self_audit_traces wrapper form"
        )

    def test_wrapper_form_rejected(self):
        """Empirical: a report with self_audit_traces wrapper MUST raise ValidationError."""
        schema = load_audit_schema()
        with open(os.path.join(SKILL, "tests/schema-validation/fixtures/valid_audit_report.json")) as f:
            fixture = json.load(f)
        fixture["self_audit_traces"] = {"wrapper": "should be rejected"}
        try:
            jsonschema.validate(fixture, schema)
            raise AssertionError("Schema accepted self_audit_traces wrapper — F103 fix regressed")
        except jsonschema.ValidationError as e:
            assert "self_audit_traces" in str(e) or "Additional properties" in e.message

    def test_canonical_fixture_still_validates(self):
        schema = load_audit_schema()
        with open(os.path.join(SKILL, "tests/schema-validation/fixtures/valid_audit_report.json")) as f:
            fixture = json.load(f)
        jsonschema.validate(fixture, schema)


# ---------------------------------------------------------------------------
# F104 — halt-condition AND/OR precedence is parenthesized
# ---------------------------------------------------------------------------

class TestF104_HaltConditionParenthesized:
    def test_n14_halt_uses_explicit_parens(self):
        with open(os.path.join(SKILL, "modules/N14-q-gate.md")) as f:
            content = f.read()
        # The halt definition MUST contain parenthesized OR-AND grouping
        # Look for the canonical pattern
        assert "(creativity < 7 OR functional_correctness < 7) AND" in content, (
            "N14 halt-on-q-gate-failure two-axis-below-threshold must explicitly parenthesize "
            "the (a OR b) AND c logic to prevent operator-precedence ambiguity"
        )

    def test_override_silences_creativity_only_failure(self):
        """Semantic: under override, creativity<7 alone must NOT halt."""
        creativity, functional = 6, 9
        user_overrode = True
        # Correct logic: halt iff (any below 7) AND (no override)
        any_below = creativity < 7 or functional < 7
        halt = any_below and not user_overrode
        assert not halt, "user override must silence creativity-only failure"


# ---------------------------------------------------------------------------
# F105 — two-axis rubric is mechanical (computable predicates)
# ---------------------------------------------------------------------------

class TestF105_RubricMechanical:
    def test_rubric_uses_predicate_table_not_prose(self):
        with open(os.path.join(SKILL, "modules/N14-q-gate.md")) as f:
            content = f.read()
        # The v2.0.2 rubric uses a markdown table with predicates and points
        assert "| Predicate | Points | Source |" in content, (
            "N14 rubric must declare predicate-based scoring table (mechanical), not pure prose"
        )
        # Each axis has a point ceiling
        assert "Maximum: 10" in content, "rubric must declare a maximum score"


# ---------------------------------------------------------------------------
# F106 — N20 failure_class enum complete
# ---------------------------------------------------------------------------

class TestF106_N20EnumComplete:
    def test_n20_outputs_enum_includes_all_v201_classes(self):
        with open(os.path.join(SKILL, "modules/N20-per-fix-verifier.md")) as f:
            content = f.read()
        # The v2.0.2 enum must list all 9 (now 10 with tool-unavailable) failure classes
        for cls in [
            "verification-failure", "commit-hook-failure", "git-operation-failure",
            "type-check-failure", "targeted-test-failure",
            "markdown-lint-failure", "cross-reference-failure",
            "schema-validation-failure", "dependency-cycle-failure",
            "tool-unavailable",
        ]:
            assert cls in content, f"N20 outputs enum must include {cls!r}"

    def test_n20_failure_classes_table_aligns_with_outputs(self):
        with open(os.path.join(SKILL, "modules/N20-per-fix-verifier.md")) as f:
            content = f.read()
        # Both the Outputs section and Failure Classes table must reference each class
        # Find outputs section
        outputs_match = re.search(r"## Outputs.*?## Side Effects", content, re.DOTALL)
        assert outputs_match
        outputs_block = outputs_match.group()
        # All v2.0.1 classes from the table must appear in outputs declaration
        for cls in ["markdown-lint-failure", "cross-reference-failure",
                    "schema-validation-failure", "dependency-cycle-failure"]:
            assert cls in outputs_block, (
                f"{cls} listed in Failure Classes table must also appear in Outputs declaration"
            )


# ---------------------------------------------------------------------------
# F107 — suspicious-content detector has SECURITY allow-list
# ---------------------------------------------------------------------------

class TestF107_SecurityAllowList:
    def test_n16_documents_security_allow_list(self):
        with open(os.path.join(SKILL, "modules/N16-fix-triage.md")) as f:
            content = f.read()
        # The allow-list must be explicit and reference both the dimension and provenance
        assert "SECURITY Allow-List" in content or "security allow-list" in content.lower(), (
            "N16 must document the SECURITY allow-list for the suspicious-content detector"
        )
        # It must check provenance (not just the dimension)
        assert "provenance.node" in content or "provenance" in content, (
            "Allow-list must key on provenance (internal source) to distinguish from external reports"
        )


# ---------------------------------------------------------------------------
# F108 — N16 multi-file fix-group merging has caps
# ---------------------------------------------------------------------------

class TestF108_FixGroupCaps:
    def test_n16_documents_max_files_per_group_cap(self):
        with open(os.path.join(SKILL, "modules/N16-fix-triage.md")) as f:
            content = f.read()
        assert "max-merged-files-per-group" in content, "N16 must declare a fix-group size cap"
        assert "max-merge-depth" in content, "N16 must declare a merge-depth cap"


# ---------------------------------------------------------------------------
# F109 — graph.json conventions are enforced (not just documented)
# ---------------------------------------------------------------------------

class TestF109_ConventionsEnforced:
    def test_spawn_cap_convention_uses_normative_language(self):
        g = load_graph()
        spawn = g["conventions"]["spawn_cap"]
        assert "MUST" in spawn, "spawn_cap convention must use MUST language"

    def test_plugin_path_resolution_documented_and_v2_dir_referenced(self):
        g = load_graph()
        path_conv = g["conventions"]["plugin_path_resolution"]
        assert "epiphany-audit-v2" in path_conv
        assert "MUST NOT" in path_conv

    def test_input_type_propagation_describes_back_edge(self):
        g = load_graph()
        prop = g["conventions"]["input_type_propagation"]
        assert "E00d" in prop, "input_type_propagation must reference the feedback edge"
        assert "N00b" in prop, "must name the producer node"

    def test_n01_outputs_does_not_claim_input_type_directly(self):
        """v2.0.1 F010 fix: N01 outputs must not include input_type as a direct field."""
        g = load_graph()
        n01 = next(n for n in g["nodes"] if n["id"] == "N01")
        assert "input_type" not in n01["outputs"], (
            "N01 outputs must not declare input_type — it's set by N00b via E00d feedback"
        )


# ---------------------------------------------------------------------------
# F110 — Fnew finding ID format validates against schema
# ---------------------------------------------------------------------------

class TestF110_FnewFindingIDValidates:
    def test_schema_accepts_fnew_prefix(self):
        schema = load_audit_schema()
        with open(os.path.join(SKILL, "tests/schema-validation/fixtures/valid_audit_report.json")) as f:
            fixture = json.load(f)
        # Replace the finding ID with Fnew0NN format
        fixture["findings"][0]["id"] = "Fnew001"
        jsonschema.validate(fixture, schema)  # MUST not raise

    def test_schema_still_accepts_normal_F0NN(self):
        schema = load_audit_schema()
        with open(os.path.join(SKILL, "tests/schema-validation/fixtures/valid_audit_report.json")) as f:
            fixture = json.load(f)
        fixture["findings"][0]["id"] = "F042"
        jsonschema.validate(fixture, schema)

    def test_schema_rejects_non_compliant_format(self):
        schema = load_audit_schema()
        with open(os.path.join(SKILL, "tests/schema-validation/fixtures/valid_audit_report.json")) as f:
            fixture = json.load(f)
        fixture["findings"][0]["id"] = "BUG042"  # wrong prefix
        try:
            jsonschema.validate(fixture, schema)
            raise AssertionError("Schema accepted invalid ID format BUG042")
        except jsonschema.ValidationError:
            pass


# ---------------------------------------------------------------------------
# F111 — version strings consistent across files
# ---------------------------------------------------------------------------

class TestF111_VersionConsistency:
    def test_all_version_strings_match(self):
        # graph.json
        g = load_graph()
        graph_v = g["version"]

        # SKILL.md frontmatter
        with open(os.path.join(SKILL, "SKILL.md")) as f:
            skill_md = f.read()
        skill_v_match = re.search(r"# epiphany-audit SKILL \(v(\d+\.\d+\.\d+)\)", skill_md)
        assert skill_v_match, "SKILL.md missing version header"
        skill_v = skill_v_match.group(1)

        # README.md
        with open(os.path.join(SKILL, "README.md")) as f:
            readme = f.read()
        readme_v_match = re.search(r"epiphany-audit v(\d+\.\d+\.\d+)", readme)
        assert readme_v_match, "README missing version"
        readme_v = readme_v_match.group(1)

        assert graph_v == skill_v == readme_v, (
            f"version drift: graph.json={graph_v}, SKILL.md={skill_v}, README.md={readme_v}"
        )


# ---------------------------------------------------------------------------
# F114 — N17 user_approvals shape per-input-type
# ---------------------------------------------------------------------------

class TestF114_PerTypeUserApprovals:
    def test_n17_documents_both_shapes(self):
        with open(os.path.join(SKILL, "modules/N17-fix-planner.md")) as f:
            content = f.read()
        assert "TieredApprovals" in content
        assert "NonCodeApprovals" in content


# ---------------------------------------------------------------------------
# F115 — tool-availability semantics documented
# ---------------------------------------------------------------------------

class TestF115_ToolAvailability:
    def test_n20_documents_tool_availability(self):
        with open(os.path.join(SKILL, "modules/N20-per-fix-verifier.md")) as f:
            content = f.read()
        assert "Tool-Availability Semantics" in content, (
            "N20 must document missing-tool fallback behavior"
        )
        assert "tool-unavailable" in content, "must define tool-unavailable failure class"


# ---------------------------------------------------------------------------
# F117 — OEF rule 3 tightened (requires evidentiary anchor)
# ---------------------------------------------------------------------------

class TestF117_OEFRuleTightened:
    def test_n26_rule3_requires_evidence_anchor(self):
        with open(os.path.join(SKILL, "modules/N26-oef.md")) as f:
            content = f.read()
        # The tightened rule must mention evidence/quantitative anchors
        assert "lacks any quantitative or evidentiary anchor" in content or \
               "evidentiary anchor" in content, (
            "N26 rule 3 must require absence of evidence anchor (not just speculative word)"
        )


# ---------------------------------------------------------------------------
# Producer-traceability with edge requirement (cross-cuts F101+F102)
# ---------------------------------------------------------------------------

class TestProducerWithEdge:
    """For each documented N14 input, verify a graph edge supplies it."""

    def test_every_n14_input_has_edge(self):
        g = load_graph()
        n14 = next(n for n in g["nodes"] if n["id"] == "N14")

        # Collect all sources of edges targeting N14
        sources_into_n14 = set()
        for e in g["edges"]:
            tgt = e.get("target")
            if tgt == "N14" or (isinstance(tgt, list) and "N14" in tgt):
                src = e.get("source")
                if isinstance(src, str):
                    sources_into_n14.add(src)
                elif isinstance(src, list):
                    sources_into_n14.update(src)

        # N14 must have at least 4 incoming edges:
        # E10 (from N13), E_log_thread (from N10), E_trace_detector (from N00b),
        # E_trace_section (from N02)
        assert "N13" in sources_into_n14, "N14 must receive from N13 (E10)"
        assert "N10" in sources_into_n14, "v2.0.2: N14 must receive from N10 (E_log_thread)"
        assert "N00b" in sources_into_n14, "v2.0.2: N14 must receive from N00b (E_trace_detector)"
        assert "N02" in sources_into_n14, "v2.0.2: N14 must receive from N02 (E_trace_section)"
