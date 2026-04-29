"""
Tests that the determinism harness can parse findings from audit reports
rendered in formats the template actually produces.

Prevents silent breakage when the template field order changes relative to
the harness regex (F006 — template-harness coupling).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "tests", "determinism"))
import re
import tempfile
import pytest


def _parse_actual_report_from_string(content: str):
    """Inline the harness parse logic so we can test it against rendered strings."""
    locations = []
    for block in re.finditer(
        r'^id: F\d+\s*\nlocation: (.+?)\s*\ndimensions: \[([^\]]+)\]',
        content, re.MULTILINE
    ):
        loc = block.group(1).strip()
        dims = [d.strip().strip("'\"") for d in block.group(2).split(",")]
        locations.append((loc, dims))
    return locations


def _write_tmp(content: str):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    f.write(content)
    f.close()
    return f.name


# --- bare YAML (no quotes) -------------------------------------------------

BARE_YAML_FINDING = """\
## Finding F001

```yaml
id: F001
location: src/parser.py:7
dimensions: [CORRECTNESS]
severity: HIGH
```
"""

def test_harness_parses_bare_yaml_dimensions():
    findings = _parse_actual_report_from_string(BARE_YAML_FINDING)
    assert findings == [("src/parser.py:7", ["CORRECTNESS"])]


def test_harness_parses_bare_yaml_multi_dimensions():
    content = """\
```yaml
id: F002
location: src/utils.py:12
dimensions: [CORRECTNESS, MAINTAINABILITY]
severity: MEDIUM
```
"""
    findings = _parse_actual_report_from_string(content)
    assert findings == [("src/utils.py:12", ["CORRECTNESS", "MAINTAINABILITY"])]


# --- JSON-style quoted dimensions ------------------------------------------

JSON_QUOTED_FINDING = """\
```yaml
id: F001
location: src/parser.py:7
dimensions: ["CORRECTNESS"]
severity: HIGH
```
"""

def test_harness_parses_json_quoted_dimensions():
    """F001 fix: d.strip().strip(\"'\\\"\") must handle JSON-quoted dim values."""
    findings = _parse_actual_report_from_string(JSON_QUOTED_FINDING)
    assert findings == [("src/parser.py:7", ["CORRECTNESS"])], (
        "Dimension comparison fails when template renders with JSON-style quotes"
    )


def test_harness_parses_python_repr_dimensions():
    """F001 fix: must handle Python-repr-style single-quoted dim values."""
    content = """\
```yaml
id: F001
location: src/parser.py:7
dimensions: ['CORRECTNESS', 'MAINTAINABILITY']
severity: HIGH
```
"""
    findings = _parse_actual_report_from_string(content)
    assert findings == [("src/parser.py:7", ["CORRECTNESS", "MAINTAINABILITY"])], (
        "Dimension comparison fails when template renders with Python-repr quotes"
    )


# --- field order contract (F006) -------------------------------------------

def test_harness_requires_id_location_dimensions_consecutive():
    """F006: template must keep id/location/dimensions on consecutive lines."""
    # Adding a field between id: and location: breaks the regex
    content = """\
```yaml
id: F001
title: some title
location: src/parser.py:7
dimensions: [CORRECTNESS]
severity: HIGH
```
"""
    findings = _parse_actual_report_from_string(content)
    # This SHOULD return zero — documenting the known fragility so a future
    # template change immediately surfaces here rather than in CI overlap %.
    assert findings == [], (
        "If this test starts failing (finds 1 result), the harness regex was "
        "updated to tolerate intervening fields — update this assertion too."
    )


# --- determinism harness end-to-end ----------------------------------------

def test_check_overlap_e2e_bare_yaml(tmp_path):
    """End-to-end: harness script scores >= 80% against python-small fixture
    when the report uses bare YAML dimension lists."""
    import importlib.util, types
    harness_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests", "determinism", "check_overlap.py"
    )
    spec = importlib.util.spec_from_file_location("check_overlap", harness_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    report = tmp_path / "report.md"
    report.write_text("""\
## Finding F001

```yaml
id: F001
location: tests/determinism/python-small/source/parser.py:6
dimensions: [CORRECTNESS]
severity: HIGH
```
""")
    actual = mod.parse_actual_report(str(report))
    fixture_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests", "determinism", "python-small"
    )
    expected = mod.load_expected.__wrapped__(fixture_dir.replace("/python-small", ""), "python-small") \
        if hasattr(mod.load_expected, "__wrapped__") else None

    if expected is None:
        import yaml
        with open(os.path.join(fixture_dir, "expected_findings.yaml")) as f:
            expected = yaml.safe_load(f)

    overlap = mod.check_overlap(actual, expected)
    assert overlap >= 0.8, f"overlap {overlap:.1%} < 80% — harness parse broken"
