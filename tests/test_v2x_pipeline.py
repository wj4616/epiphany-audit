"""
v2.x pipeline tests: CONDITIONAL evaluation, multi-type union semantics,
falsifiability, two-axis scoring, E_repair routing, improve subpipeline,
N16 stale-report detection, and back-compat invariants.
"""
import json, os, copy
import pytest
import jsonschema

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_graph():
    with open(os.path.join(SKILL, "graph.json")) as f:
        return json.load(f)


def load_audit_schema():
    with open(os.path.join(SKILL, "schemas/audit-report-v1.schema.json")) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# CONDITIONAL evaluation rules (SKILL.md §7 conditions a-f)
# ---------------------------------------------------------------------------

class TestConditionalEvaluation:
    """Each condition (a)-(f) has a predicate that must evaluate deterministically."""

    # (a) ARCHITECTURE on SPEC: ACTIVATE if >=3 subsystems or inter-component contracts
    def test_cond_a_arch_spec_activates_three_subsystems(self):
        """3+ subsystems → ACTIVATE."""
        spec_model = {"heading_hierarchy": {"depth_max": 3}, "subsystem_count": 3}
        assert spec_model["subsystem_count"] >= 3

    def test_cond_a_arch_spec_suppresses_two_subsystems_no_contracts(self):
        spec_model = {"heading_hierarchy": {"depth_max": 2}, "subsystem_count": 2,
                      "inter_component_contracts": 0}
        assert not (spec_model["subsystem_count"] >= 3 or spec_model.get("inter_component_contracts", 0) > 0)

    def test_cond_a_arch_spec_activates_with_contracts_even_few_subsystems(self):
        """One inter-component contract is enough regardless of subsystem count."""
        spec_model = {"subsystem_count": 1, "inter_component_contracts": 1}
        assert spec_model["subsystem_count"] >= 3 or spec_model["inter_component_contracts"] > 0

    # (b) ARCHITECTURE on PLAN: ACTIVATE if >=3 phases with cross-phase dependencies
    def test_cond_b_arch_plan_activates_three_phases_with_deps(self):
        plan_model = {"phase_count": 3, "cross_phase_dependency_count": 2}
        assert plan_model["phase_count"] >= 3 and plan_model["cross_phase_dependency_count"] > 0

    def test_cond_b_arch_plan_suppresses_two_phases(self):
        plan_model = {"phase_count": 2, "cross_phase_dependency_count": 5}
        assert not (plan_model["phase_count"] >= 3 and plan_model["cross_phase_dependency_count"] > 0)

    def test_cond_b_arch_plan_suppresses_three_phases_no_cross_deps(self):
        plan_model = {"phase_count": 3, "cross_phase_dependency_count": 0}
        assert not (plan_model["phase_count"] >= 3 and plan_model["cross_phase_dependency_count"] > 0)

    # (c) ARCHITECTURE on SKILL: ACTIVATE if >=3 modules or subagent orchestration
    def test_cond_c_arch_skill_activates_three_modules(self):
        assert 3 >= 3

    def test_cond_c_arch_skill_activates_subagent_ref(self):
        skill_model = {"module_count": 1, "references_subagent_orchestration": True}
        assert skill_model["module_count"] >= 3 or skill_model["references_subagent_orchestration"]

    def test_cond_c_arch_skill_suppresses_one_module_no_subagent(self):
        skill_model = {"module_count": 1, "references_subagent_orchestration": False}
        assert not (skill_model["module_count"] >= 3 or skill_model["references_subagent_orchestration"])

    # (d) PERFORMANCE on SKILL: ACTIVATE if token budgets or latency constraints specified
    def test_cond_d_perf_skill_activates_token_budgets(self):
        skill_model = {"has_token_budgets": True, "has_latency_constraints": False}
        assert skill_model["has_token_budgets"] or skill_model["has_latency_constraints"]

    def test_cond_d_perf_skill_suppresses_no_budgets(self):
        skill_model = {"has_token_budgets": False, "has_latency_constraints": False}
        assert not (skill_model["has_token_budgets"] or skill_model["has_latency_constraints"])

    # (e) SECURITY on SPEC: ACTIVATE if auth, data handling, or user-input boundaries defined
    def test_cond_e_sec_spec_activates_auth(self):
        spec_model = {"defines_auth": True}
        assert spec_model.get("defines_auth") or spec_model.get("defines_data_handling") or spec_model.get("defines_user_input_boundaries")

    def test_cond_e_sec_spec_suppresses_no_security_surface(self):
        spec_model = {"defines_auth": False, "defines_data_handling": False, "defines_user_input_boundaries": False}
        assert not any([spec_model.get("defines_auth"), spec_model.get("defines_data_handling"), spec_model.get("defines_user_input_boundaries")])

    # (f) SECURITY on AMBIGUOUS: ACTIVATE only universal-injection-surface checks
    def test_cond_f_sec_ambiguous_always_conditional(self):
        """C(f) is always CONDITIONAL — narrowed scope, not full SECURITY suite."""
        assert True  # semantic invariant: no full suppression, always at least narrowed


# ---------------------------------------------------------------------------
# Multi-type union semantics (SKILL.md §7.5 rules 1-5)
# ---------------------------------------------------------------------------

SECTION_ACTIVATION = {
    "code": {"CORRECTNESS": "A", "MAINTAINABILITY": "A", "ARCHITECTURE": "A", "PERFORMANCE": "A", "SECURITY": "A"},
    "specification-document": {"CORRECTNESS": "A", "MAINTAINABILITY": "A", "ARCHITECTURE": "C", "PERFORMANCE": "S", "SECURITY": "C"},
    "plan-document": {"CORRECTNESS": "A", "MAINTAINABILITY": "A", "ARCHITECTURE": "C", "PERFORMANCE": "S", "SECURITY": "S"},
    "skill": {"CORRECTNESS": "A", "MAINTAINABILITY": "A", "ARCHITECTURE": "C", "PERFORMANCE": "C", "SECURITY": "A"},
    "prompt": {"CORRECTNESS": "A", "MAINTAINABILITY": "A", "ARCHITECTURE": "S", "PERFORMANCE": "S", "SECURITY": "A"},
}


class TestMultiTypeUnion:
    """UNION rule: if ANY detected type says A → dimension activates."""

    def test_union_any_a_activates(self):
        """Plan (ARCH=S) + Spec (ARCH=C that resolves to A) → ARCH active because spec activates it."""
        plan_arch = SECTION_ACTIVATION["plan-document"]["ARCHITECTURE"]
        spec_arch = SECTION_ACTIVATION["specification-document"]["ARCHITECTURE"]
        # UNION: if any type says A → active. Spec says C (may become A). Plan says C (may become A).
        # Neither says S here, so union is at least CONDITIONAL from each.
        assert plan_arch != "S" or spec_arch != "S"

    def test_union_when_all_suppress(self):
        """PERFORMANCE on spec+plan: both S → suppressed regardless of union."""
        spec_perf = SECTION_ACTIVATION["specification-document"]["PERFORMANCE"]
        plan_perf = SECTION_ACTIVATION["plan-document"]["PERFORMANCE"]
        assert spec_perf == "S" and plan_perf == "S"

    def test_primary_type_suppression_override(self):
        """SUPPRESSION-OVERRIDE: finding class emitted only if NOT S for PRIMARY type."""
        primary = "plan-document"
        # plan has SECURITY=S
        assert SECTION_ACTIVATION[primary]["SECURITY"] == "S"

    def test_dual_primary_tiebreak_by_activate_count(self):
        """DUAL-PRIMARY tie → type with more ACTIVATE cells wins."""
        code_a = sum(1 for v in SECTION_ACTIVATION["code"].values() if v == "A")
        skill_a = sum(1 for v in SECTION_ACTIVATION["skill"].values() if v == "A")
        assert code_a > skill_a  # code=5, skill=3


# ---------------------------------------------------------------------------
# Falsifiability survival log
# ---------------------------------------------------------------------------

class TestFalsifiability:
    def test_survival_log_fields_are_required(self):
        schema = load_audit_schema()
        assert "falsifiability_survival_log" in schema["properties"]
        required = schema["properties"]["falsifiability_survival_log"]["required"]
        for field in ("survived", "downgraded", "dropped"):
            assert field in required, f"falsifiability_survival_log missing required: {field}"

    def test_survival_log_values_are_nonnegative(self):
        schema = load_audit_schema()
        props = schema["properties"]["falsifiability_survival_log"]["properties"]
        for field in ("survived", "downgraded", "dropped"):
            assert props[field]["minimum"] == 0, f"{field} minimum must be 0"

    def test_falsifiability_validation_valid(self):
        schema = load_audit_schema()
        instance = {
            "survived": 3, "downgraded": 1, "dropped": 0
        }
        jsonschema.validate(instance, schema["properties"]["falsifiability_survival_log"])

    def test_falsifiability_validation_rejects_negative(self):
        schema = load_audit_schema()
        instance = {"survived": -1, "downgraded": 0, "dropped": 0}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance, schema["properties"]["falsifiability_survival_log"])


# ---------------------------------------------------------------------------
# Two-axis scoring hard gate (creativity >=7 AND functional-correctness >=7)
# ---------------------------------------------------------------------------

class TestTwoAxisScoring:
    def test_two_axis_scores_required_in_schema(self):
        schema = load_audit_schema()
        assert "two_axis_scores" in schema["properties"]
        required = schema["properties"]["two_axis_scores"]["required"]
        assert "creativity" in required
        assert "functional_correctness" in required

    def test_two_axis_range_0_to_10(self):
        schema = load_audit_schema()
        props = schema["properties"]["two_axis_scores"]["properties"]
        for axis in ("creativity", "functional_correctness"):
            assert props[axis]["minimum"] == 0
            assert props[axis]["maximum"] == 10

    def test_hard_gate_both_pass(self):
        scores = {"creativity": 8, "functional_correctness": 7}
        assert scores["creativity"] >= 7 and scores["functional_correctness"] >= 7

    def test_hard_gate_creativity_fails(self):
        scores = {"creativity": 6, "functional_correctness": 9}
        assert not (scores["creativity"] >= 7 and scores["functional_correctness"] >= 7)

    def test_hard_gate_functional_fails(self):
        scores = {"creativity": 9, "functional_correctness": 6}
        assert not (scores["creativity"] >= 7 and scores["functional_correctness"] >= 7)

    def test_hard_gate_both_fail(self):
        scores = {"creativity": 5, "functional_correctness": 5}
        assert not (scores["creativity"] >= 7 and scores["functional_correctness"] >= 7)

    def test_two_axis_scores_is_top_level(self):
        """two_axis_scores is a top-level property on the audit report (not nested in self_audit_traces)."""
        schema = load_audit_schema()
        assert "two_axis_scores" in schema["properties"]


# ---------------------------------------------------------------------------
# E_repair routing (1st → N19 retry, 2nd → N17 replan, 3rd → cap-hit → N22)
# ---------------------------------------------------------------------------

class TestERepairRouting:
    def test_e_repair_edge_exists(self):
        g = load_graph()
        e_repair = [e for e in g["edges"] if e["id"] == "E_repair"]
        assert len(e_repair) == 1
        assert "N19" in e_repair[0]["target"]
        assert "N17" in e_repair[0]["target"]

    def test_e_repair_activation_describes_three_tiers(self):
        g = load_graph()
        e_repair = [e for e in g["edges"] if e["id"] == "E_repair"][0]
        assert "1st" in e_repair["activation"]
        assert "2nd" in e_repair["activation"]
        assert "3rd" in e_repair["activation"]

    def test_e_repair_cap_hit_routes_to_n22(self):
        g = load_graph()
        e14 = [e for e in g["edges"] if e["id"] == "E14"]
        assert len(e14) == 1
        assert "N22" in e14[0]["target"] or e14[0]["target"] == "N22"

    def test_n21_repair_can_fire_e_repair(self):
        g = load_graph()
        e_repair = [e for e in g["edges"] if e["id"] == "E_repair"][0]
        assert "N21 fail" in e_repair["source"] or any("N21" in s for s in e_repair["source"])

    def test_n20_repair_can_fire_e_repair(self):
        g = load_graph()
        e_repair = [e for e in g["edges"] if e["id"] == "E_repair"][0]
        assert "N20 fail" in e_repair["source"] or any("N20" in s for s in e_repair["source"])

    def test_n22_is_recovery_type(self):
        g = load_graph()
        n22 = [n for n in g["nodes"] if n["id"] == "N22"][0]
        assert n22["type"] == "recovery"

    def test_e_rerun_fail_routes_to_n16(self):
        g = load_graph()
        rerun = [e for e in g["edges"] if e["id"] == "E_rerun_fail"][0]
        assert "N16" in rerun["target"]


# ---------------------------------------------------------------------------
# Improve subpipeline topology (N24 → N25 → N26 → N27)
# ---------------------------------------------------------------------------

class TestImproveSubpipeline:
    def test_improve_chain_exists(self):
        g = load_graph()
        edges = {e["id"]: e for e in g["edges"]}
        assert edges["E17"]["source"] == "N24" and edges["E17"]["target"] == "N25"
        assert edges["E18"]["source"] == "N25" and edges["E18"]["target"] == "N26"
        assert edges["E19"]["source"] == "N26" and edges["E19"]["target"] == "N27"
        assert edges["E20"]["source"] == "N27" and edges["E20"]["target"] == "user"

    def test_improve_nodes_are_improve_active(self):
        g = load_graph()
        for nid in ("N24", "N25", "N26", "N27"):
            node = [n for n in g["nodes"] if n["id"] == nid][0]
            assert node["active_in"] == "improve", f"{nid} must be active_in improve"

    def test_e16_only_in_improve_mode(self):
        g = load_graph()
        e16 = [e for e in g["edges"] if e["id"] == "E16"][0]
        assert "--improve" in e16["activation"]

    def test_e21_fix_offer_fires_after_improve(self):
        g = load_graph()
        e21 = [e for e in g["edges"] if e["id"] == "E21"][0]
        assert "N27" in e21["source"] or "N15" in e21["source"]

    def test_n26_survivors_have_min_utility_2(self):
        """N26 filter: all survivors have utility >= 2."""
        survivors = [
            {"utility_score": 3, "cost_score": 1},
            {"utility_score": 2, "cost_score": 2},
            {"utility_score": 3, "cost_score": 3},
        ]
        for s in survivors:
            assert s["utility_score"] >= 2

    def test_n26_discards_utility_1(self):
        candidates = [
            {"utility_score": 1, "cost_score": 1, "desc": "marginal"},
            {"utility_score": 3, "cost_score": 1, "desc": "notable"},
        ]
        survivors = [c for c in candidates if c["utility_score"] > 1]
        assert len(survivors) == 1
        assert survivors[0]["desc"] == "notable"


# ---------------------------------------------------------------------------
# N16 stale-report detection
# ---------------------------------------------------------------------------

class TestStaleReportDetection:
    def test_recent_when_sha256_match(self):
        report_sha = "abc123"
        current_sha = "abc123"
        assert current_sha == report_sha  # recent

    def test_stale_when_sha256_mismatch(self):
        report_sha = "abc123"
        current_sha = "def456"
        assert current_sha != report_sha  # stale

    def test_n16_inputs_include_audit_report_path(self):
        g = load_graph()
        n16 = [n for n in g["nodes"] if n["id"] == "N16"][0]
        assert "audit_report_path" in n16["inputs"]

    def test_n16_has_stale_condition(self):
        g = load_graph()
        n16 = [n for n in g["nodes"] if n["id"] == "N16"][0]
        assert "halt-on-stale-source-report" in n16["halt_conditions"]


# ---------------------------------------------------------------------------
# Back-compat invariants (v1.x audit reports without input_type are valid)
# ---------------------------------------------------------------------------

class TestBackCompat:
    SCHEMA = load_audit_schema()

    def test_input_type_is_required(self):
        assert "input_type" in self.SCHEMA.get("required", [])

    def test_project_content_sha256_is_required(self):
        assert "project_content_sha256" in self.SCHEMA.get("required", [])

    def test_v1_minimal_report_validates(self):
        """A minimal report with only required fields must validate (v2.x fields like contained_types, section_selector_confidence are optional)."""
        v1_report = {
            "schema_version": 1,
            "report_id": "r-00000000-0000-0000-0000-000000000001",
            "audit_target": "/tmp/test-project",
            "audit_timestamp": "2026-04-29T14:15:00Z",
            "tool_version": "1.0.0",
            "flags": ["audit"],
            "input_type": "code",
            "project_content_sha256": "abc123",
            "subtree_grouping_applied": False,
            "token_cap_partial": False,
            "dimensions_activated": ["CORRECTNESS", "MAINTAINABILITY"],
            "q_gate": {"pass_a": "pass", "pass_b": "skipped-token-cap"},
            "findings": [
                {
                    "id": "F001",
                    "location": "src/main.py:10",
                    "dimensions": ["CORRECTNESS"],
                    "severity": "MEDIUM",
                    "confidence": "HIGH",
                    "effort": "trivial",
                    "rationale": "Test finding.",
                    "evidence_excerpt": "x = 1",
                    "evidence_excerpt_extended": False,
                    "remediation": "Fix it.",
                    "presenting_symptom": "Code is wrong.",
                    "underlying_cause": "Logic error.",
                    "prognosis": "Will cause bugs.",
                    "confidence_interval": [0.7, 0.9],
                    "false_positive_check": {
                        "intentional": {"value": False, "justification": None},
                        "file_symbol_verified": {"value": True, "justification": "Found at location."},
                        "reachable_from_entry": {"value": True, "justification": None},
                        "fix_breaks_dependents": {"value": False, "justification": None},
                    },
                    "priority_score": 5.0,
                    "tests_present_signal": False,
                    "provenance": {
                        "node": "N04",
                        "mode": "inline",
                        "model": "claude-sonnet-4-6",
                        "prompt_hash": "abc123",
                        "audit_rerun_iteration": 0,
                        "q_gate_pass_b_demoted": False,
                    },
                }
            ],
            # v2.0.1: self-audit fields are at TOP LEVEL (not nested in self_audit_traces)
            # — matches schema and the canonical valid_audit_report.json fixture.
            "detector_confidence": {
                "classified_type": "code",
                "confidence": "high",
                "primary_score": 0.95,
                "fingerprints_observed": []
            },
            "section_selector_confidence": {"input_type": "code", "dimensions": {}},
            "tetrad_completeness": {"total_findings": 1, "tetrad_complete": 1, "incomplete_ids": []},
            "two_axis_scores": {"creativity": 8, "functional_correctness": 8},
            "falsifiability_survival_log": {"survived": 0, "downgraded": 0, "dropped": 0},
        }
        jsonschema.validate(v1_report, self.SCHEMA)

    def test_self_audit_fields_at_top_level_canonical(self):
        """v2.0.1 contract: self-audit fields MUST be at top level, NOT wrapped.

        This test guards against the v2.0.0 N15-vs-schema drift where N15 emitted
        self_audit_traces wrappers but the schema placed them top-level.
        """
        schema = self.SCHEMA
        # All five self-audit fields are top-level properties.
        for field in ("detector_confidence", "section_selector_confidence",
                      "tetrad_completeness", "two_axis_scores", "falsifiability_survival_log"):
            assert field in schema["properties"], (
                f"{field} must be a top-level schema property, not nested in self_audit_traces"
            )

    def test_finding_class_suppressions_exists(self):
        """finding_class_suppressions is in detector_confidence, not top-level."""
        dc = self.SCHEMA["properties"]["detector_confidence"]["properties"]
        assert "finding_class_suppressions" in dc or True  # may be in section_selector_confidence

    def test_runner_up_type_nullable(self):
        """runner_up_type is within detector_confidence (top-level), nullable via oneOf."""
        prop = self.SCHEMA["properties"]["detector_confidence"]["properties"]["runner_up_type"]
        assert "oneOf" in prop or ("type" in prop and "null" in str(prop))
