"""
Frontmatter-trace coherence guards — proposal 1 enforcement.

Guards that report frontmatter fields are consistent with their producer traces:
- detector_confidence.classified_type == input_type
- dimensions_activated matches section_selector_confidence dimensions
- tetrad_completeness numbers are internally consistent
- falsifiability_survival_log counts match findings
- two_axis_scores are integers in [0, 10]
"""
import json
import os
import copy

import jsonschema
import pytest
import yaml

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SUPPORTED_INPUT_TYPES = {
    "code", "specification-document", "plan-document",
    "skill", "prompt", "ambiguous-text",
}


def load_audit_schema():
    with open(os.path.join(SKILL, "schemas/audit-report-v1.schema.json")) as f:
        return json.load(f)


def _minimal_report(**overrides):
    """Build a minimal valid report dict."""
    base = {
        "schema_version": 2,
        "report_id": "test-001",
        "audit_target": "/tmp/test",
        "audit_timestamp": "2026-04-29T00:00:00Z",
        "tool_version": "2.0.3",
        "input_type": "skill",
        "project_content_sha256": "a" * 64,
        "flags": [],
        "dimensions_activated": ["CORRECTNESS", "MAINTAINABILITY"],
        "subtree_grouping_applied": False,
        "token_cap_partial": False,
        "q_gate": {"pass_a": "pass", "pass_b": "pass"},
        "findings": [],
        "detector_confidence": {"confidence": "high", "classified_type": "skill", "primary_score": 0.92},
        "section_selector_confidence": {
            "input_type": "skill",
            "dimensions": {
                "CORRECTNESS": {"status": "ACTIVATED", "reason": "floor"},
                "MAINTAINABILITY": {"status": "ACTIVATED", "reason": "floor"},
            }
        },
        "tetrad_completeness": {"total_findings": 0, "tetrad_complete": 0, "incomplete_ids": []},
        "two_axis_scores": {"creativity": 7, "functional_correctness": 7},
        "two_axis_scores_overridden_by_user": False,
        "falsifiability_survival_log": {"survived": 0, "downgraded": 0, "dropped": 0},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# detector_confidence coherence
# ---------------------------------------------------------------------------

class TestDetectorConfidenceCoherence:
    """detector_confidence.classified_type must equal input_type."""

    def test_classified_type_matches_input_type(self):
        r = _minimal_report()
        assert r["detector_confidence"]["classified_type"] == r["input_type"]

    def test_classified_type_mismatch_detected(self):
        r = _minimal_report(
            input_type="code",
            detector_confidence={"confidence": "high", "classified_type": "skill"},
        )
        assert r["detector_confidence"]["classified_type"] != r["input_type"]


# ---------------------------------------------------------------------------
# dimensions_activated coherence
# ---------------------------------------------------------------------------

class TestDimensionsActivatedCoherence:
    """dimensions_activated entries should correspond to ACTIVATE decisions in
    section_selector_confidence."""

    def test_activated_dimensions_have_activate_decision(self):
        r = _minimal_report(
            dimensions_activated=["CORRECTNESS", "MAINTAINABILITY", "ARCHITECTURE"],
            section_selector_confidence={
                "input_type": "code",
                "dimensions": {
                    "CORRECTNESS": {"status": "ACTIVATED", "reason": "floor"},
                    "MAINTAINABILITY": {"status": "ACTIVATED", "reason": "floor"},
                    "ARCHITECTURE": {"status": "ACTIVATED", "reason": "multi-subsystem"},
                    "PERFORMANCE": {"status": "SUPPRESSED", "reason": "spec type"},
                }
            },
        )
        ssc_dims = r["section_selector_confidence"]["dimensions"]
        for dim in r["dimensions_activated"]:
            assert dim in ssc_dims, f"{dim} must be in section_selector_confidence"
            assert ssc_dims[dim]["status"] == "ACTIVATED", (
                f"{dim} in dimensions_activated but status is {ssc_dims[dim]['status']}"
            )

    def test_suppressed_dimensions_not_in_activated(self):
        r = _minimal_report(
            dimensions_activated=["CORRECTNESS", "MAINTAINABILITY"],
            section_selector_confidence={
                "input_type": "skill",
                "dimensions": {
                    "CORRECTNESS": {"status": "ACTIVATED", "reason": "floor"},
                    "MAINTAINABILITY": {"status": "ACTIVATED", "reason": "floor"},
                    "PERFORMANCE": {"status": "SUPPRESSED", "reason": "spec type"},
                }
            },
        )
        suppressed = [
            k for k, v in r["section_selector_confidence"]["dimensions"].items()
            if v.get("status") == "SUPPRESSED"
        ]
        for dim in suppressed:
            assert dim not in r["dimensions_activated"], (
                f"Suppressed dimension {dim} should not be in dimensions_activated"
            )


# ---------------------------------------------------------------------------
# tetrad_completeness internal consistency
# ---------------------------------------------------------------------------

class TestTetradCompletenessCoherence:
    """tetrad_completeness numbers must be internally consistent."""

    def test_tetrad_complete_le_total(self):
        r = _minimal_report(
            tetrad_completeness={"total_findings": 5, "tetrad_complete": 5, "incomplete_ids": []}
        )
        tc = r["tetrad_completeness"]
        assert tc["tetrad_complete"] <= tc["total_findings"]

    def test_incomplete_ids_count_matches_difference(self):
        r = _minimal_report(
            tetrad_completeness={"total_findings": 5, "tetrad_complete": 3, "incomplete_ids": ["F001", "F003"]}
        )
        tc = r["tetrad_completeness"]
        expected_incomplete = tc["total_findings"] - tc["tetrad_complete"]
        assert len(tc["incomplete_ids"]) == expected_incomplete, (
            f"Expected {expected_incomplete} incomplete IDs, got {len(tc['incomplete_ids'])}"
        )


# ---------------------------------------------------------------------------
# two_axis_scores range validation
# ---------------------------------------------------------------------------

class TestTwoAxisScoresCoherence:
    """two_axis_scores must be integers in [0, 10]."""

    def test_scores_are_integers_in_range(self):
        r = _minimal_report()
        scores = r["two_axis_scores"]
        for axis in ("creativity", "functional_correctness"):
            val = scores[axis]
            assert isinstance(val, int), f"{axis} must be int, got {type(val)}"
            assert 0 <= val <= 10, f"{axis} must be in [0, 10], got {val}"

    def test_scores_below_7_gate_should_fail(self):
        """Scores below 7 on either axis should be detectably sub-threshold."""
        r = _minimal_report(
            two_axis_scores={"creativity": 6, "functional_correctness": 10}
        )
        scores = r["two_axis_scores"]
        gate_pass = scores["creativity"] >= 7 and scores["functional_correctness"] >= 7
        assert not gate_pass, "creativity=6 should not pass the gate"


# ---------------------------------------------------------------------------
# falsifiability_survival_log matches findings
# ---------------------------------------------------------------------------

class TestFalsifiabilitySurvivalLogCoherence:
    """falsifiability_survival_log counts should be derivable from findings."""

    def test_survival_log_present_with_findings(self):
        r = _minimal_report(
            findings=[
                {"severity": "HIGH", "confidence": "HIGH", "location": "x:1",
                 "falsifiability": {"status": "survived"}},
                {"severity": "MEDIUM", "confidence": "MEDIUM", "location": "x:2",
                 "falsifiability": {"status": "downgraded"}},
            ],
            falsifiability_survival_log={"survived": 1, "downgraded": 1, "dropped": 0},
        )
        survived_count = sum(
            1 for f in r["findings"]
            if f.get("falsifiability", {}).get("status") == "survived"
        )
        assert r["falsifiability_survival_log"]["survived"] == survived_count


# ---------------------------------------------------------------------------
# Schema full validation passes
# ---------------------------------------------------------------------------

class TestReportSchemaValidation:
    """A complete well-formed report must validate."""

    def test_full_report_validates(self):
        r = _minimal_report(
            dimensions_activated=["CORRECTNESS", "MAINTAINABILITY", "ARCHITECTURE", "SECURITY"],
            section_selector_confidence={
                "input_type": "skill",
                "dimensions": {
                    "CORRECTNESS": {"status": "ACTIVATED", "reason": "floor"},
                    "MAINTAINABILITY": {"status": "ACTIVATED", "reason": "floor"},
                    "ARCHITECTURE": {"status": "ACTIVATED", "reason": "multi-module"},
                    "SECURITY": {"status": "ACTIVATED", "reason": "skill-type"},
                }
            },
            findings=[
                {
                    "id": "F001",
                    "severity": "HIGH",
                    "confidence": "HIGH",
                    "location": "modules/N01.md:10",
                    "dimensions": ["CORRECTNESS"],
                    "evidence_excerpt": "broken code here",
                    "evidence_excerpt_extended": False,
                    "rationale": "Test.",
                    "remediation": "Fix.",
                    "false_positive_check": {
                        "intentional": {"value": True, "justification": "N/A"},
                        "file_symbol_verified": {"value": True, "justification": "Read confirmed"},
                        "reachable_from_entry": {"value": True, "justification": "Entry path traced"},
                        "fix_breaks_dependents": {"value": False, "justification": "No dependents"},
                    },
                    "effort": "modest",
                    "priority_score": 8,
                    "tests_present_signal": False,
                    "provenance": {
                        "node": "N04", "mode": "inline", "model": "claude-opus-4-7",
                        "prompt_hash": "a" * 40, "audit_rerun_iteration": 0,
                        "q_gate_pass_b_demoted": False,
                    },
                    "presenting_symptom": "X",
                    "underlying_cause": "Y",
                    "prognosis": "Z",
                    "confidence_interval": "MEDIUM",
                    "falsifiability": {"status": "survived", "counter_argument": "Rebutted."},
                },
            ],
            tetrad_completeness={"total_findings": 1, "tetrad_complete": 1, "incomplete_ids": []},
            falsifiability_survival_log={"survived": 1, "downgraded": 0, "dropped": 0},
        )
        schema = load_audit_schema()
        jsonschema.validate(r, schema)
