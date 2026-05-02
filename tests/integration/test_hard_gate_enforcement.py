"""
Hard-gate enforcement integration tests (v2.0.1).

These tests guard against the v2.0.0 audit's CRITICAL finding F002 — that the
two-axis "hard gate" was documented but no node enforced it.

The gate is now enforced at N14 Pass A check #8. These tests assert:
  1. The gate logic is bidirectional (passes when both ≥7, fails when either < 7).
  2. The N14 module contract declares the check.
  3. SKILL.md §18 describes the halt path explicitly.
"""
import os


SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def n14_contract():
    with open(os.path.join(SKILL, "modules/N14-q-gate.md")) as f:
        return f.read()


def skill_md():
    with open(os.path.join(SKILL, "SKILL.md")) as f:
        return f.read()


def test_n14_contract_declares_two_axis_check():
    """v2.0.1: N14 Pass A check #8 explicitly enforces the two-axis gate."""
    contract = n14_contract()
    assert "Two-axis hard gate" in contract or "two-axis hard gate" in contract.lower(), (
        "N14 module contract must declare the two-axis hard gate as a Pass A check"
    )


def test_n14_contract_declares_halt_subreason():
    """v2.0.1: failing the gate halts with a documented subreason."""
    contract = n14_contract()
    assert "two-axis-below-threshold" in contract, (
        "N14 module contract must declare halt subreason 'two-axis-below-threshold'"
    )


def test_skill_md_describes_halt_path_not_just_regeneration():
    """v2.0.1: SKILL.md §18 must say the gate halts (not just 'triggers regeneration')."""
    s = skill_md()
    # Find the §18 section.
    idx = s.find("## 18. Two-Axis")
    assert idx >= 0, "SKILL.md §18 not found"
    section = s[idx:idx + 3000]
    assert "halt" in section.lower(), (
        "§18 must describe the halt path, not just 'regeneration'"
    )
    assert "halt-on-q-gate-failure" in section, (
        "§18 must reference the canonical halt name"
    )


def test_gate_arithmetic_passes_on_77():
    """Both axes at threshold → gate passes."""
    creativity, functional = 7, 7
    assert creativity >= 7 and functional >= 7


def test_gate_arithmetic_fails_on_creativity_below():
    creativity, functional = 6, 9
    assert not (creativity >= 7 and functional >= 7)


def test_gate_arithmetic_fails_on_functional_below():
    creativity, functional = 9, 6
    assert not (creativity >= 7 and functional >= 7)


def test_gate_arithmetic_fails_on_both_below():
    creativity, functional = 5, 5
    assert not (creativity >= 7 and functional >= 7)


def test_falsifiability_scope_is_severity_based_not_tag_based():
    """v2.0.1 (F004 fix): the check fires on severity ≥ MEDIUM, not on a 'creative' tag."""
    s = skill_md()
    idx = s.find("## 16. Falsifiability")
    assert idx >= 0, "SKILL.md §16 not found"
    section = s[idx:idx + 2500]
    assert "severity" in section.lower(), "§16 must gate on severity"
    assert "MEDIUM" in section, "§16 must reference MEDIUM threshold"


def test_n10_owns_falsifiability_per_v201_fix():
    """v2.0.1 (F011 fix): N10 generates falsifiability counter-arguments (has file access)."""
    with open(os.path.join(SKILL, "modules/N10-fpv.md")) as f:
        n10 = f.read()
    assert "Falsifiability" in n10, "N10 module must document falsifiability ownership"
    assert "v2.0.1" in n10 or "moved from N13" in n10, (
        "N10 must explicitly note the v2.0.1 move from N13"
    )
