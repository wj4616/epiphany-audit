"""
Halt condition naming convention guards — proposal 1 enforcement.

Guards the contract: "All halt IDs MUST start with 'halt-'. Pattern:
halt-<timing>-<condition> where timing is on/pre/mid/suspicious/ambiguous/no."
"""
import json
import os
import re

import yaml

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HALT_PATTERN = re.compile(r"^halt-(on|pre|mid|suspicious|ambiguous|no)-")
HALT_ID_RE = re.compile(r"`(halt-[a-z-]+)`")

# Module files to scan for halt conditions
MODULE_DIR = os.path.join(SKILL, "modules")


def _gather_halt_ids_from_modules():
    """Extract all halt IDs from module ## Halt Conditions sections."""
    halt_ids: dict[str, set[str]] = {}
    for fname in sorted(os.listdir(MODULE_DIR)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(MODULE_DIR, fname)
        text = open(fpath).read()
        ids = set()
        for m in HALT_ID_RE.finditer(text):
            ids.add(m.group(1))
        if ids:
            halt_ids[fname] = ids
    return halt_ids


def _gather_halt_ids_from_skill():
    """Extract halt IDs referenced in SKILL.md."""
    skill_path = os.path.join(SKILL, "SKILL.md")
    text = open(skill_path).read()
    return set(m.group(1) for m in HALT_ID_RE.finditer(text))


def _gather_halt_ids_from_graph():
    """Extract halt IDs from graph.json halt_condition_naming convention + nodes."""
    with open(os.path.join(SKILL, "graph.json")) as f:
        g = json.load(f)
    ids = set()
    for node in g.get("nodes", []):
        for hc in node.get("halt_conditions", []):
            if isinstance(hc, str):
                ids.add(hc)
            elif isinstance(hc, dict):
                ids.add(hc.get("id", ""))
    # Also check conventions block
    return ids


# ---------------------------------------------------------------------------
# Naming convention compliance
# ---------------------------------------------------------------------------

class TestHaltNamingConvention:
    """Every halt ID must match ^halt-(on|pre|mid|suspicious|ambiguous|no)-."""

    def test_all_module_halt_ids_match_convention(self):
        module_halt_ids = _gather_halt_ids_from_modules()
        violations = []
        for fname, ids in module_halt_ids.items():
            for hid in ids:
                if not HALT_PATTERN.match(hid):
                    violations.append(f"{fname}: {hid}")
        assert not violations, (
            f"Halt IDs violating naming convention:\n" + "\n".join(violations)
        )

    def test_skill_md_halt_ids_match_convention(self):
        skill_ids = _gather_halt_ids_from_skill()
        violations = [hid for hid in skill_ids if not HALT_PATTERN.match(hid)]
        assert not violations, (
            f"SKILL.md halt IDs violating naming convention: {violations}"
        )


# ---------------------------------------------------------------------------
# No duplicate halt IDs across modules
# ---------------------------------------------------------------------------

class TestHaltUniqueness:
    """No two modules should define the same halt condition (one owner each)."""

    def test_no_duplicate_halt_ids_across_modules(self):
        # These halt IDs are legitimately referenced by multiple modules
        # because they're triggered in multiple pipeline phases
        shared_halts = {
            "halt-on-user-abort", "halt-on-flag-conflict",
            "halt-on-baseline-failure", "halt-on-recovery-conflict",
            "halt-on-scope-creep",
        }

        module_halt_ids = _gather_halt_ids_from_modules()
        seen: dict[str, list[str]] = {}
        for fname, ids in module_halt_ids.items():
            for hid in ids:
                if hid in shared_halts:
                    continue
                seen.setdefault(hid, []).append(fname)

        duplicates = {hid: files for hid, files in seen.items() if len(files) > 1}
        assert not duplicates, (
            f"Duplicate halt IDs across modules: {duplicates}"
        )


# ---------------------------------------------------------------------------
# Every halt referenced in SKILL.md exists in a module
# ---------------------------------------------------------------------------

class TestHaltCoverage:
    """Hall halt IDs referenced in SKILL.md should be defined in at least one module."""

    def test_skill_md_halt_ids_exist_in_modules(self):
        skill_ids = _gather_halt_ids_from_skill()
        module_halt_ids = _gather_halt_ids_from_modules()
        all_module_ids = set()
        for ids in module_halt_ids.values():
            all_module_ids |= ids

        orphans = skill_ids - all_module_ids
        # Some halt IDs may be defined in graph.json conventions, not modules
        graph_ids = _gather_halt_ids_from_graph()
        true_orphans = orphans - graph_ids

        assert not true_orphans, (
            f"Halt IDs in SKILL.md not found in any module: {true_orphans}"
        )


# ---------------------------------------------------------------------------
# Halt condition count sanity
# ---------------------------------------------------------------------------

class TestHaltCount:
    """There should be at least 25 distinct halt conditions (current: ~28+)."""

    def test_minimum_halt_count(self):
        module_halt_ids = _gather_halt_ids_from_modules()
        all_ids = set()
        for ids in module_halt_ids.values():
            all_ids |= ids
        assert len(all_ids) >= 25, (
            f"Expected ≥25 distinct halt conditions across modules, got {len(all_ids)}"
        )
