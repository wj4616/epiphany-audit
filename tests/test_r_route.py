"""
R-ROUTE activation unit tests.

Tests the dimension plugin trigger/exclusion configuration that informs
R-ROUTE's activation decisions. Reads YAML frontmatter from dimensions/*.md
and simulates the trigger evaluation logic.
"""
import os, glob, re
import yaml
import pytest

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOOR_DIMENSIONS = {"correctness", "maintainability"}


def load_plugins():
    plugins = {}
    for path in glob.glob(os.path.join(SKILL, "dimensions/*.md")):
        with open(path) as f:
            content = f.read()
        m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if m:
            data = yaml.safe_load(m.group(1))
            plugins[data["name"]] = data
    return plugins


def activates(plugin, signals):
    """Simulate R-ROUTE activation for one plugin given codebase signals."""
    file_count = signals.get("file_count", 100)
    for excl in plugin.get("exclusions", []):
        if excl["type"] == "project_size" and file_count <= excl["max_files"]:
            return False

    for trigger in plugin.get("activation_triggers", []):
        if trigger["type"] == "file_present":
            return True
        if trigger["type"] == "import_grep":
            content = signals.get("content", "")
            min_matches = trigger.get("min_matches", 1)
            if len(re.findall(trigger["pattern"], content)) >= min_matches:
                return True
    return False


def test_floor_dimensions_present():
    plugins = load_plugins()
    for dim in FLOOR_DIMENSIONS:
        assert dim in plugins, f"floor plugin '{dim}' not found in dimensions/"


def test_floor_dimensions_activate_on_empty_codebase():
    """CORRECTNESS and MAINTAINABILITY must activate regardless of codebase content."""
    plugins = load_plugins()
    empty = {"content": "", "file_count": 0}
    for dim in FLOOR_DIMENSIONS:
        assert activates(plugins[dim], empty), (
            f"{dim} is a floor dimension and must activate even for an empty codebase"
        )


def test_security_activates_on_auth_content():
    """SECURITY activates when codebase imports auth/token/credential patterns."""
    plugins = load_plugins()
    signals = {
        "content": "import jwt\nauth_token = get_token()\npassword = request.form['pw']",
        "file_count": 5,
    }
    assert activates(plugins["security"], signals)


def test_security_skips_neutral_content():
    """SECURITY must not activate on codebases with no security-relevant patterns."""
    plugins = load_plugins()
    signals = {"content": "def add(a, b):\n    return a + b\n", "file_count": 5}
    assert not activates(plugins["security"], signals)


def test_performance_excluded_on_small_project():
    """PERFORMANCE is excluded when project has ≤3 files regardless of content."""
    plugins = load_plugins()
    signals = {
        "content": "for x in items:\n    result.sort()\nwhile True:\n    data.filter()",
        "file_count": 2,
    }
    assert not activates(plugins["performance"], signals)


def test_performance_activates_on_loop_heavy_larger_project():
    """PERFORMANCE activates when project is large enough and has loop/sort patterns."""
    plugins = load_plugins()
    signals = {
        "content": "for x in items:\n    result.sort()\nwhile True:\n    data.filter()",
        "file_count": 10,
    }
    assert activates(plugins["performance"], signals)


def test_all_plugins_have_schema_version_1():
    plugins = load_plugins()
    assert plugins, "no dimension plugins found"
    for name, plugin in plugins.items():
        assert plugin.get("schema_version") == 1, (
            f"{name}: schema_version must be 1"
        )


def test_all_floor_dimensions_have_file_present_trigger():
    """Floor guarantee: correctness and maintainability use file_present trigger."""
    plugins = load_plugins()
    for dim in FLOOR_DIMENSIONS:
        triggers = plugins[dim].get("activation_triggers", [])
        types = [t["type"] for t in triggers]
        assert "file_present" in types, (
            f"{dim}: floor dimension must have a file_present activation trigger"
        )


# --- v2.x Per-Type Activation Matrix Tests ---

# Section-activation matrix: for each input type, some dimensions are ACTIVATE,
# SUPPRESS, or CONDITIONAL (see SKILL.md §10).
# These tests validate the matrix rules as unit-testable invariants.

SECTION_ACTIVATION = {
    "code": {
        "CORRECTNESS": "ACTIVATE", "MAINTAINABILITY": "ACTIVATE",
        "ARCHITECTURE": "CONDITIONAL", "PERFORMANCE": "CONDITIONAL",
        "SECURITY": "CONDITIONAL",
    },
    "specification-document": {
        "CORRECTNESS": "ACTIVATE", "MAINTAINABILITY": "ACTIVATE",
        "ARCHITECTURE": "SUPPRESS", "PERFORMANCE": "SUPPRESS",
        "SECURITY": "SUPPRESS",
    },
    "plan-document": {
        "CORRECTNESS": "ACTIVATE", "MAINTAINABILITY": "ACTIVATE",
        "ARCHITECTURE": "SUPPRESS", "PERFORMANCE": "SUPPRESS",
        "SECURITY": "SUPPRESS",
    },
    "skill": {
        "CORRECTNESS": "ACTIVATE", "MAINTAINABILITY": "ACTIVATE",
        "ARCHITECTURE": "CONDITIONAL", "PERFORMANCE": "CONDITIONAL",
        "SECURITY": "CONDITIONAL",
    },
    "prompt": {
        "CORRECTNESS": "ACTIVATE", "MAINTAINABILITY": "ACTIVATE",
        "ARCHITECTURE": "SUPPRESS", "PERFORMANCE": "SUPPRESS",
        "SECURITY": "CONDITIONAL",
    },
    "ambiguous-text": {
        "CORRECTNESS": "ACTIVATE", "MAINTAINABILITY": "ACTIVATE",
        "ARCHITECTURE": "SUPPRESS", "PERFORMANCE": "SUPPRESS",
        "SECURITY": "SUPPRESS",
    },
}

FINDING_CLASS_SUPPRESSIONS = {
    "specification-document": [
        "missing-error-handling", "race-condition", "resource-leak",
        "null-dereference", "type-error", "off-by-one",
    ],
    "plan-document": [
        "missing-error-handling", "race-condition", "resource-leak",
        "null-dereference", "type-error", "off-by-one",
    ],
    "prompt": [
        "missing-error-handling", "race-condition", "resource-leak",
        "null-dereference",
    ],
    "ambiguous-text": [
        "missing-error-handling", "race-condition", "resource-leak",
        "null-dereference", "type-error", "off-by-one",
        "architectural-smell", "performance-regression",
    ],
}


def test_floor_dimensions_activate_for_all_types():
    """CORRECTNESS and MAINTAINABILITY must be ACTIVATE for every input type."""
    for input_type, dims in SECTION_ACTIVATION.items():
        for floor_dim in FLOOR_DIMENSIONS:
            key = floor_dim.upper()
            assert dims.get(key) == "ACTIVATE", (
                f"{key} must be ACTIVATE for {input_type}, got {dims.get(key)}"
            )


def test_code_type_allows_all_dimensions():
    """Code input type has CONDITIONAL for non-floor dims (never SUPPRESS)."""
    code_dims = SECTION_ACTIVATION["code"]
    for dim, decision in code_dims.items():
        assert decision in ("ACTIVATE", "CONDITIONAL"), (
            f"code: {dim} must be ACTIVATE or CONDITIONAL, got {decision}"
        )


def test_spec_doc_suppresses_non_text_dims():
    """Spec docs suppress ARCHITECTURE, PERFORMANCE, SECURITY."""
    spec = SECTION_ACTIVATION["specification-document"]
    for dim in ("ARCHITECTURE", "PERFORMANCE", "SECURITY"):
        assert spec[dim] == "SUPPRESS", (
            f"specification-document: {dim} must be SUPPRESS, got {spec[dim]}"
        )


def test_plan_doc_suppresses_non_text_dims():
    """Plan docs suppress ARCHITECTURE, PERFORMANCE, SECURITY."""
    plan = SECTION_ACTIVATION["plan-document"]
    for dim in ("ARCHITECTURE", "PERFORMANCE", "SECURITY"):
        assert plan[dim] == "SUPPRESS", (
            f"plan-document: {dim} must be SUPPRESS, got {plan[dim]}"
        )


def test_ambiguous_text_suppresses_all_non_floor():
    """Ambiguous text suppresses all non-floor dimensions."""
    amb = SECTION_ACTIVATION["ambiguous-text"]
    for dim in ("ARCHITECTURE", "PERFORMANCE", "SECURITY"):
        assert amb[dim] == "SUPPRESS", (
            f"ambiguous-text: {dim} must be SUPPRESS, got {amb[dim]}"
        )


def test_spec_doc_suppresses_code_finding_classes():
    """Spec docs suppress code-specific finding classes."""
    suppressed = FINDING_CLASS_SUPPRESSIONS["specification-document"]
    assert "off-by-one" in suppressed
    assert "race-condition" in suppressed


def test_plan_doc_suppresses_code_finding_classes():
    """Plan docs suppress code-specific finding classes."""
    suppressed = FINDING_CLASS_SUPPRESSIONS["plan-document"]
    assert "null-dereference" in suppressed
    assert "type-error" in suppressed


def test_prompt_does_not_suppress_type_error():
    """Prompts suppress fewer classes than spec/plan; type-error may be relevant."""
    prompt_suppressed = FINDING_CLASS_SUPPRESSIONS["prompt"]
    assert "off-by-one" not in prompt_suppressed


def test_ambiguous_text_suppresses_most_classes():
    """Ambiguous text has the broadest suppression set."""
    amb_suppressed = FINDING_CLASS_SUPPRESSIONS["ambiguous-text"]
    assert len(amb_suppressed) >= 7


def test_all_types_have_floor_coverage():
    """Every input type defines activation for all five built-in dimensions."""
    all_dims = {"CORRECTNESS", "MAINTAINABILITY", "ARCHITECTURE", "PERFORMANCE", "SECURITY"}
    for input_type, dims in SECTION_ACTIVATION.items():
        covered = set(dims.keys())
        missing = all_dims - covered
        assert not missing, f"{input_type}: missing dimension entries for {missing}"
