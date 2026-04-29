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
