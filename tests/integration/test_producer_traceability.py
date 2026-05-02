"""
Producer-traceability integration tests (v2.0.1).

These tests guard against the v2.0.0 audit's CRITICAL finding F003 — that three
top-level schema fields (tetrad_completeness, two_axis_scores,
falsifiability_survival_log) had no documented producer in any module contract.

Each schema-defined optional self-audit field MUST be claimed as an output by at
least one node in graph.json (or, for fields produced by upstream nodes and only
threaded through, claimed in N14's outputs as part of the pre-save fix-up).
"""
import json
import os
import re

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_graph():
    with open(os.path.join(SKILL, "graph.json")) as f:
        return json.load(f)


def load_audit_schema():
    with open(os.path.join(SKILL, "schemas/audit-report-v1.schema.json")) as f:
        return json.load(f)


def collect_all_outputs():
    """All output identifiers declared by any node in graph.json (flattened)."""
    g = load_graph()
    outputs = set()
    for node in g["nodes"]:
        for o in node.get("outputs", []):
            outputs.add(o)
    return outputs


def test_tetrad_completeness_has_producer():
    """N14 Q-GATE Pass A check #2 produces tetrad_completeness."""
    outputs = collect_all_outputs()
    assert "tetrad_completeness" in outputs, (
        "tetrad_completeness is a top-level schema field with no node-output declaration. "
        "Add it to N14's outputs."
    )


def test_two_axis_scores_has_producer():
    """N14 Q-GATE Pass A check #8 produces two_axis_scores."""
    outputs = collect_all_outputs()
    assert "two_axis_scores" in outputs, (
        "two_axis_scores is a top-level schema field with no node-output declaration. "
        "Add it to N14's outputs."
    )


def test_falsifiability_survival_log_has_producer():
    """N10 FPV produces falsifiability_survival_log (v2.0.1 — moved from N13)."""
    outputs = collect_all_outputs()
    assert "falsifiability_survival_log" in outputs, (
        "falsifiability_survival_log is a top-level schema field with no producer. "
        "Add it to N10's outputs (N10 owns the falsifiability check post-v2.0.1)."
    )


def test_detector_confidence_trace_has_producer():
    """N00b InputTypeDetector produces detector_confidence_trace."""
    outputs = collect_all_outputs()
    assert "detector_confidence_trace" in outputs, (
        "detector_confidence_trace must be declared as an N00b output."
    )


def test_n14_inputs_include_traces_for_coherence_check():
    """v2.0.1: Q-GATE Pass A check #9 (frontmatter-trace coherence) needs the traces."""
    g = load_graph()
    n14 = next(n for n in g["nodes"] if n["id"] == "N14")
    inputs = n14["inputs"]
    assert "detector_confidence_trace" in inputs, (
        "N14 must receive detector_confidence_trace as input for coherence check"
    )
    assert "section_selector_confidence" in inputs, (
        "N14 must receive section_selector_confidence as input for coherence check"
    )


def test_n14_halt_conditions_cover_two_axis_gate():
    """v2.0.1: the hard gate must be enforced — N14 declares the halt subreason."""
    g = load_graph()
    n14 = next(n for n in g["nodes"] if n["id"] == "N14")
    notes = n14.get("notes", "")
    assert "two-axis-below-threshold" in notes, (
        "N14 notes must document the two-axis-below-threshold halt subreason"
    )


def test_n10_falsifiability_documented():
    """v2.0.1: falsifiability check moved from N13 to N10 (which has source-file access)."""
    g = load_graph()
    n10 = next(n for n in g["nodes"] if n["id"] == "N10")
    notes = n10.get("notes", "")
    assert "falsifiability" in notes.lower(), (
        "N10 notes must document the v2.0.1 falsifiability move"
    )


def test_plugin_path_uses_skill_dir_relative_resolution():
    """F001 fix: graph.json conventions document <skill_dir>-relative path resolution."""
    g = load_graph()
    convention = g["conventions"].get("plugin_path_resolution", "")
    assert "<skill_dir>" in convention or "skill_dir" in convention, (
        "graph.json conventions must document plugin path resolution to prevent v1-path bugs"
    )
    assert "epiphany-audit-v2" in convention, (
        "convention must reference the v2 directory explicitly"
    )


def test_spawn_cap_documented_in_conventions():
    """F015 fix: shared spawn cap declared at graph level, not buried in N04 prose."""
    g = load_graph()
    assert "spawn_cap" in g["conventions"], (
        "graph.json conventions must declare the shared spawn cap for N04..N09"
    )


def test_n02_does_not_hardcode_v1_path():
    """F001 fix: N02 module contract must not reference the v1 SKILL dimensions path.

    The user-config path `~/.config/epiphany-audit/dimensions/` is unrelated and
    correct — only the skill-bundled path is at risk.
    """
    n02_path = os.path.join(SKILL, "modules/N02-r-route.md")
    with open(n02_path) as f:
        content = f.read()
    # Match ONLY the skill-bundled v1 path; ignore the user config dir.
    bad_pattern = r"~/\.claude/skills/epiphany-audit/dimensions"
    for line in content.split("\n"):
        if re.search(bad_pattern, line) and "epiphany-audit-v2/dimensions" not in line:
            assert "MUST NOT" in line or "v1 path" in line, (
                f"N02 references the v1 dimensions path outside a 'MUST NOT' warning: {line!r}"
            )
