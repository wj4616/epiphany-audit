#!/usr/bin/env python3
"""
Determinism harness for epiphany-audit.

Usage:
  python tests/determinism/check_overlap.py <actual-audit-report.md> [--fixture python-small]

Parses the actual audit report's finding locations and defect classes, compares against
the frozen expected_findings.yaml, and reports the set-overlap percentage.
Exits 1 if overlap is below 80% (for non-optional expected findings).
"""
import sys, os, re, yaml, argparse

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_expected(fixture_name):
    path = os.path.join(SKILL, f"tests/determinism/{fixture_name}/expected_findings.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def parse_actual_report(report_path):
    """Extract (location, dimension) pairs from an audit report."""
    with open(report_path) as f:
        content = f.read()
    # Extract finding locations from yaml blocks
    locations = []
    for block in re.finditer(r'^id: F\d+\s*\nlocation: (.+?)\s*\ndimensions: \[([^\]]+)\]',
                              content, re.MULTILINE):
        loc = block.group(1).strip()
        dims = [d.strip().strip("'\"") for d in block.group(2).split(",")]
        locations.append((loc, dims))
    return locations


def check_overlap(actual_findings, expected):
    """Return overlap fraction (0.0–1.0) for non-optional expected findings."""
    required = [f for f in expected["expected_findings"] if not f.get("optional")]
    if not required:
        print("No required expected findings; overlap check trivially passes.")
        return 1.0

    matched = 0
    for exp in required:
        exp_loc_prefix = exp["location"].removeprefix("source/")
        for (actual_loc, actual_dims) in actual_findings:
            loc_matches = exp_loc_prefix in actual_loc
            dim_matches = exp["dimension"] in actual_dims
            if loc_matches and dim_matches:
                matched += 1
                break

    overlap = matched / len(required)
    return overlap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report_path")
    parser.add_argument("--fixture", default="python-small")
    args = parser.parse_args()

    expected = load_expected(args.fixture)
    actual = parse_actual_report(args.report_path)

    overlap = check_overlap(actual, expected)
    pct = overlap * 100
    threshold = 80.0

    print(f"Set-overlap: {pct:.1f}% (threshold: {threshold}%)")
    if pct < threshold:
        print(f"FAIL: overlap {pct:.1f}% is below the {threshold}% CI gate threshold.")
        sys.exit(1)
    else:
        print(f"PASS: overlap {pct:.1f}% meets the {threshold}% CI gate.")


if __name__ == "__main__":
    main()
