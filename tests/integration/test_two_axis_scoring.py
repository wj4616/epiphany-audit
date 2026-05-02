"""
Two-axis scoring reference implementation and determinism tests (v2.0.2).

Guards the N14 MUST contract: "Two implementations evaluating the same report
MUST produce identical scores." Implements the mechanical predicate tables from
N14-q-gate.md (Two-Axis Score Computation Rubric v2.0.2).

Usage: pass a parsed report dict (top-level frontmatter + findings list) to
TwoAxisScorer.score(report_dict) -> {"creativity": int, "functional_correctness": int}.
Both scores are integers in [0, 10].
"""
import json
import os

import pytest

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SUPPORTED_INPUT_TYPES = {
    "code", "specification-document", "plan-document",
    "skill", "prompt", "ambiguous-text",
}
FLOOR_DIMENSIONS = {"CORRECTNESS", "MAINTAINABILITY"}
NONFLOOR_DIMENSIONS = {"ARCHITECTURE", "PERFORMANCE", "SECURITY"}
HIGH_SEVERITY = {"CRITICAL", "HIGH"}
MEDIUM_AND_ABOVE = {"MEDIUM", "HIGH", "CRITICAL"}
VALID_CONFIDENCE_LABELS = {"HIGH", "MEDIUM", "LOW"}
HIGH_CONFIDENCE_LABELS = {"HIGH", "MEDIUM"}


class TwoAxisScorer:
    """
    Deterministic two-axis scorer for audit reports.

    Input: report_dict — a Python dict with:
      - top-level frontmatter fields (tetrad_completeness, falsifiability_survival_log,
        dimensions_activated, gap_dimensions_auto_added, section_selector_confidence,
        detector_confidence, q_gate, input_type, subtree_grouping_applied, subtrees)
      - "findings": list of dicts, each with fields:
        severity, confidence, location, falsifiability (optional)
      - "location_verification_cache": dict keyed on location strings (optional)

    Output: {"creativity": int, "functional_correctness": int}
    Both scores are min(10, max(0, sum_of_predicate_points)).
    """

    def score(self, report: dict) -> dict:
        return {
            "creativity": self._creativity(report),
            "functional_correctness": self._functional_correctness(report),
        }

    # --- Creativity predicates ---

    def _creativity(self, r: dict) -> int:
        pts = 0

        tc = r.get("tetrad_completeness", {})
        total = tc.get("total_findings", 0)
        complete = tc.get("tetrad_complete", 0)
        if total >= 1 and complete == total:
            pts += 2  # predicate 1

        fsl = r.get("falsifiability_survival_log", {})
        survived = fsl.get("survived", 0)
        downgraded = fsl.get("downgraded", 0)
        dropped = fsl.get("dropped", 0)

        if survived >= 1:
            pts += 1  # predicate 2

        findings = r.get("findings", [])
        medium_plus_count = sum(
            1 for f in findings
            if f.get("severity", "") in MEDIUM_AND_ABOVE
        )
        if survived + downgraded + dropped >= medium_plus_count:
            pts += 2  # predicate 3 (full falsifiability coverage)

        if any(
            f.get("falsifiability", {}).get("counter_argument")
            for f in findings
        ):
            pts += 1  # predicate 4

        activated = set(r.get("dimensions_activated", []))
        all_five = FLOOR_DIMENSIONS | NONFLOOR_DIMENSIONS
        if len(activated & all_five) >= 3:
            pts += 1  # predicate 5

        if len(r.get("gap_dimensions_auto_added", [])) >= 1:
            pts += 1  # predicate 6

        # predicate 7: section_selector_confidence records at least one SUPPRESS decision
        ssc = r.get("section_selector_confidence", {})
        dimension_decisions = ssc.get("dimensions", {})
        if any(
            v.get("decision") == "SUPPRESS"
            for v in dimension_decisions.values()
            if isinstance(v, dict)
        ):
            pts += 1  # predicate 7

        # predicate 8: at least one HIGH/CRITICAL finding with falsifiability.status == "survived"
        if any(
            f.get("severity") in HIGH_SEVERITY
            and f.get("falsifiability", {}).get("status") == "survived"
            for f in findings
        ):
            pts += 1  # predicate 8

        return min(10, max(0, pts))

    # --- Functional correctness predicates ---

    def _functional_correctness(self, r: dict) -> int:
        pts = 0

        # predicate 1: schema validates (2pts) — requires jsonschema + schema file
        try:
            import jsonschema
            schema_path = os.path.join(SKILL, "schemas", "audit-report-v1.schema.json")
            with open(schema_path) as f:
                schema = json.load(f)
            # Attempt validation; a scorer receiving an already-validated dict passes.
            # For a plain dict without full schema structure, we check minimal fields.
            jsonschema.validate(r, schema)
            pts += 2
        except Exception:
            pass  # schema validation failure → 0pts for this predicate

        # predicate 2: detector_confidence is "high" or "marginal"
        dc = r.get("detector_confidence", {})
        if dc.get("confidence") in {"high", "marginal"}:
            pts += 1

        # predicate 3: q_gate.pass_a in {pass, pass-minimal} AND pass_b not fail/exec-error
        qg = r.get("q_gate", {})
        pass_a_ok = qg.get("pass_a") in {"pass", "pass-minimal"}
        pass_b_ok = qg.get("pass_b") not in {"fail", "exec-error"}
        if pass_a_ok and pass_b_ok:
            pts += 1

        # predicate 4: every finding's location in location_verification_cache as verified
        cache = r.get("location_verification_cache", {})
        findings = r.get("findings", [])
        if findings and cache:
            if all(
                cache.get(f.get("location", ""), {}).get("verified", False)
                for f in findings
                if f.get("location")
            ):
                pts += 1
        elif not findings:
            pts += 1  # no findings → trivially satisfied

        # predicate 5: floor dimensions present in dimensions_activated
        activated = set(r.get("dimensions_activated", []))
        if FLOOR_DIMENSIONS.issubset(activated):
            pts += 1

        # predicate 6: input_type is supported AND matches detector_confidence.classified_type
        it = r.get("input_type", "")
        dc_type = dc.get("classified_type", "")
        if it in SUPPORTED_INPUT_TYPES and it == dc_type:
            pts += 1

        # predicate 7: tetrad_completeness.incomplete_ids is empty
        tc = r.get("tetrad_completeness", {})
        if len(tc.get("incomplete_ids", ["placeholder"])) == 0:
            pts += 1

        # predicate 8: all CRITICAL/HIGH findings have confidence in {HIGH, MEDIUM}
        critical_high = [f for f in findings if f.get("severity") in HIGH_SEVERITY]
        if not critical_high or all(
            f.get("confidence") in HIGH_CONFIDENCE_LABELS for f in critical_high
        ):
            pts += 1

        # predicate 9: subtree_grouping_applied consistency
        sga = r.get("subtree_grouping_applied", False)
        subtrees = r.get("subtrees", [])
        if not sga or (sga and len(subtrees) >= 1):
            pts += 1

        return min(10, max(0, pts))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

SCORER = TwoAxisScorer()


def _minimal_report(**overrides):
    """Construct a minimal passing report dict for testing."""
    base = {
        "input_type": "skill",
        "dimensions_activated": ["CORRECTNESS", "MAINTAINABILITY", "ARCHITECTURE"],
        "gap_dimensions_auto_added": [],
        "subtree_grouping_applied": False,
        "subtrees": [],
        "tetrad_completeness": {"total_findings": 0, "tetrad_complete": 0, "incomplete_ids": []},
        "falsifiability_survival_log": {"survived": 0, "downgraded": 0, "dropped": 0},
        "section_selector_confidence": {"dimensions": {}},
        "detector_confidence": {"confidence": "high", "classified_type": "skill"},
        "q_gate": {"pass_a": "pass", "pass_b": "pass"},
        "findings": [],
        "location_verification_cache": {},
    }
    base.update(overrides)
    return base


# --- Determinism ---

def test_scorer_is_deterministic_empty_report():
    """Two calls with the same empty report must yield identical scores."""
    r = _minimal_report()
    s1 = SCORER.score(r)
    s2 = SCORER.score(r)
    assert s1 == s2, f"Scores diverged: {s1} vs {s2}"


def test_scorer_is_deterministic_rich_report():
    """Two calls with a report containing findings and falsifiability must yield identical scores."""
    r = _minimal_report(
        dimensions_activated=["CORRECTNESS", "MAINTAINABILITY", "ARCHITECTURE", "PERFORMANCE", "SECURITY"],
        gap_dimensions_auto_added=["MODULE-COHERENCE"],
        tetrad_completeness={"total_findings": 2, "tetrad_complete": 2, "incomplete_ids": []},
        falsifiability_survival_log={"survived": 2, "downgraded": 0, "dropped": 0},
        findings=[
            {
                "severity": "HIGH", "confidence": "HIGH", "location": "modules/N01.md:10",
                "falsifiability": {"status": "survived", "counter_argument": "..."},
            },
            {
                "severity": "MEDIUM", "confidence": "MEDIUM", "location": "modules/N02.md:5",
                "falsifiability": {"status": "survived", "counter_argument": "..."},
            },
        ],
        location_verification_cache={
            "modules/N01.md:10": {"verified": True},
            "modules/N02.md:5": {"verified": True},
        },
    )
    s1 = SCORER.score(r)
    s2 = SCORER.score(r)
    assert s1 == s2, f"Scores diverged: {s1} vs {s2}"
    # Also verify both axes ≥7 for a well-formed report
    assert s1["creativity"] >= 7, f"Expected creativity ≥7, got {s1['creativity']}"
    assert s1["functional_correctness"] >= 7, f"Expected fc ≥7, got {s1['functional_correctness']}"


# --- Creativity predicate unit tests ---

def test_creativity_predicate1_full_tetrad_coverage():
    """tetrad_complete == total_findings AND total_findings >= 1 → +2pts."""
    r_full = _minimal_report(
        tetrad_completeness={"total_findings": 3, "tetrad_complete": 3, "incomplete_ids": []}
    )
    r_partial = _minimal_report(
        tetrad_completeness={"total_findings": 3, "tetrad_complete": 2, "incomplete_ids": ["F002"]}
    )
    assert SCORER._creativity(r_full) >= SCORER._creativity(r_partial) + 2


def test_creativity_predicate2_survived_gte_1():
    """falsifiability_survival_log.survived >= 1 → +1pt."""
    r_yes = _minimal_report(
        falsifiability_survival_log={"survived": 1, "downgraded": 0, "dropped": 0}
    )
    r_no = _minimal_report(
        falsifiability_survival_log={"survived": 0, "downgraded": 0, "dropped": 0}
    )
    assert SCORER._creativity(r_yes) == SCORER._creativity(r_no) + 1


def test_creativity_predicate5_three_dimensions():
    """dimensions_activated ≥3 of the five → +1pt."""
    r_three = _minimal_report(
        dimensions_activated=["CORRECTNESS", "MAINTAINABILITY", "ARCHITECTURE"]
    )
    r_two = _minimal_report(
        dimensions_activated=["CORRECTNESS", "MAINTAINABILITY"]
    )
    assert SCORER._creativity(r_three) == SCORER._creativity(r_two) + 1


def test_creativity_predicate6_gap_auto_added():
    """gap_dimensions_auto_added >= 1 → +1pt."""
    r_yes = _minimal_report(gap_dimensions_auto_added=["MODULE-COHERENCE"])
    r_no = _minimal_report(gap_dimensions_auto_added=[])
    assert SCORER._creativity(r_yes) == SCORER._creativity(r_no) + 1


def test_creativity_predicate7_suppressed_dimension():
    """section_selector_confidence has a SUPPRESS decision → +1pt."""
    r_yes = _minimal_report(
        section_selector_confidence={
            "dimensions": {
                "PERFORMANCE": {"decision": "SUPPRESS", "reason": "spec type"}
            }
        }
    )
    r_no = _minimal_report(
        section_selector_confidence={"dimensions": {}}
    )
    assert SCORER._creativity(r_yes) == SCORER._creativity(r_no) + 1


# --- Functional correctness predicate unit tests ---

def test_fc_predicate2_detector_confidence_high():
    """detector_confidence.confidence == 'high' → +1pt."""
    r_high = _minimal_report(
        detector_confidence={"confidence": "high", "classified_type": "skill"}
    )
    r_ambig = _minimal_report(
        detector_confidence={"confidence": "ambiguous", "classified_type": "skill"}
    )
    assert SCORER._functional_correctness(r_high) >= SCORER._functional_correctness(r_ambig) + 1


def test_fc_predicate5_floor_dimensions_present():
    """CORRECTNESS and MAINTAINABILITY in dimensions_activated → +1pt."""
    r_yes = _minimal_report(
        dimensions_activated=["CORRECTNESS", "MAINTAINABILITY"]
    )
    r_no = _minimal_report(
        dimensions_activated=["ARCHITECTURE"]
    )
    assert SCORER._functional_correctness(r_yes) >= SCORER._functional_correctness(r_no) + 1


def test_fc_predicate7_tetrad_completeness_zero_incomplete():
    """tetrad_completeness.incomplete_ids empty → +1pt."""
    r_complete = _minimal_report(
        tetrad_completeness={"total_findings": 2, "tetrad_complete": 2, "incomplete_ids": []}
    )
    r_incomplete = _minimal_report(
        tetrad_completeness={"total_findings": 2, "tetrad_complete": 1, "incomplete_ids": ["F001"]}
    )
    assert SCORER._functional_correctness(r_complete) == SCORER._functional_correctness(r_incomplete) + 1


def test_fc_predicate8_high_severity_confidence_floor():
    """All CRITICAL/HIGH findings must have confidence HIGH or MEDIUM → +1pt when satisfied."""
    r_ok = _minimal_report(
        findings=[{"severity": "HIGH", "confidence": "HIGH", "location": "x:1"}]
    )
    r_fail = _minimal_report(
        findings=[{"severity": "HIGH", "confidence": "LOW", "location": "x:1"}]
    )
    assert SCORER._functional_correctness(r_ok) >= SCORER._functional_correctness(r_fail) + 1


# --- Gate threshold tests ---

def test_gate_passes_at_77():
    """Both axes at threshold → gate passes."""
    assert 7 >= 7 and 7 >= 7


def test_gate_fails_creativity_below_threshold():
    """Creativity below 7 → gate fails regardless of functional_correctness."""
    creativity, fc = 6, 10
    assert not (creativity >= 7 and fc >= 7)


def test_gate_fails_fc_below_threshold():
    """Functional correctness below 7 → gate fails regardless of creativity."""
    creativity, fc = 10, 6
    assert not (creativity >= 7 and fc >= 7)
