"""
Schema version 2 validation guards — proposal 3 enforcement.

Guards that all 5 JSON schemas accept schema_version=2 and that
dimension plugins declare schema_version=2 in their frontmatter.
"""
import json
import os
import re

import jsonschema
import pytest
import yaml

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCHEMA_FILES = [
    "audit-report-v1.schema.json",
    "dimension-plugin-v1.schema.json",
    "dry-run-plan-v1.schema.json",
    "fix-report-v1.schema.json",
    "improvement-report-v1.schema.json",
]

DIMENSION_PLUGINS = [
    "correctness.md",
    "architecture.md",
    "performance.md",
    "security.md",
    "maintainability.md",
]


def load_schema(name):
    with open(os.path.join(SKILL, "schemas", name)) as f:
        return json.load(f)


def load_dimension_plugin(name):
    """Parse YAML frontmatter from a dimension plugin .md file."""
    text = open(os.path.join(SKILL, "dimensions", name)).read()
    # Extract frontmatter between --- markers
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        raise ValueError(f"No frontmatter found in {name}")
    return yaml.safe_load(m.group(1))


# ---------------------------------------------------------------------------
# Schema version const = 2
# ---------------------------------------------------------------------------

class TestSchemaVersionConst:
    """Every JSON schema must have schema_version.const == 2."""

    @pytest.mark.parametrize("schema_file", SCHEMA_FILES)
    def test_schema_version_const_is_2(self, schema_file):
        s = load_schema(schema_file)
        sv = s["properties"]["schema_version"]
        assert sv.get("const") == 2, (
            f"{schema_file} schema_version.const must be 2, got {sv.get('const')}"
        )


# ---------------------------------------------------------------------------
# Minimal valid documents with schema_version=2
# ---------------------------------------------------------------------------

class TestSchemaAcceptsVersion2:
    """Minimal documents with schema_version=2 must validate against each schema."""

    def test_audit_report_accepts_schema_version_2(self):
        s = load_schema("audit-report-v1.schema.json")
        doc = {
            "schema_version": 2,
            "report_id": "test-report-001",
            "audit_target": "/tmp/test",
            "audit_timestamp": "2026-04-29T00:00:00Z",
            "tool_version": "2.0.3",
            "input_type": "code",
            "project_content_sha256": "a" * 64,
            "flags": [],
            "dimensions_activated": ["CORRECTNESS", "MAINTAINABILITY"],
            "subtree_grouping_applied": False,
            "token_cap_partial": False,
            "q_gate": {"pass_a": "pass", "pass_b": "pass"},
            "findings": [],
        }
        jsonschema.validate(doc, s)

    def test_dimension_plugin_accepts_schema_version_2(self):
        s = load_schema("dimension-plugin-v1.schema.json")
        doc = {
            "schema_version": 2,
            "name": "test-dim",
            "display_name": "Test Dimension",
            "version": "1.0.0",
            "applies_to": {"languages": "*", "project_markers": [], "input_types": ["code"]},
            "activation_triggers": [{"type": "file_present", "path": "**/*"}],
            "exclusions": [],
            "prompt_template": "Analyze the target.",
            "kb_route_query": None,
            "intra_node_token_budget": 10000,
            "priority": "medium",
        }
        jsonschema.validate(doc, s)

    def test_dry_run_plan_accepts_schema_version_2(self):
        s = load_schema("dry-run-plan-v1.schema.json")
        doc = {
            "schema_version": 2,
            "plan_id": "plan-001",
            "source_audit_report": "/tmp/report.md",
            "source_audit_report_sha256": "a" * 64,
            "source_report_id": "rpt-001",
            "plan_timestamp": "2026-04-29T00:00:00Z",
            "flags": ["dry-run"],
            "triage_summary": {
                "total_findings": 0,
                "tier_1_count": 0,
                "tier_2_count": 0,
                "tier_3_count": 0,
                "deferred_at_triage": 0,
                "conflicting_groups": [],
            },
            "simulated_branch": "fix/test",
            "body": [],
        }
        jsonschema.validate(doc, s)

    def test_fix_report_accepts_schema_version_2(self):
        s = load_schema("fix-report-v1.schema.json")
        doc = {
            "schema_version": 2,
            "fix_report_id": "fix-001",
            "partial": False,
            "halt_state": None,
            "source_audit_report": "/tmp/report.md",
            "source_audit_report_sha256": "a" * 64,
            "source_report_id": "rpt-001",
            "fix_run_timestamp": "2026-04-29T00:00:00Z",
            "branch": "fix/test",
            "flags": [],
            "test_command_used": "pytest",
            "audit_rerun_delta": {"scope": "full"},
            "diff_scope_check": "pass",
            "unmapped_hunks": [],
            "recovery_manifest_ref": None,
            "last_known_good_sha": "b" * 40,
            "body": [],
        }
        jsonschema.validate(doc, s)

    def test_improvement_report_accepts_schema_version_2(self):
        s = load_schema("improvement-report-v1.schema.json")
        doc = {
            "schema_version": 2,
            "improvement_report_id": "imp-001",
            "source_audit_report": "/tmp/report.md",
            "source_audit_report_sha256": "a" * 64,
            "source_report_id": "rpt-001",
            "audit_target": "/tmp/test",
            "improvement_timestamp": "2026-04-29T00:00:00Z",
            "tool_version": "2.0.3",
            "flags": ["improve"],
            "improvement_partial": False,
            "total_candidates": 5,
            "filtered_out": 2,
            "survivors": 3,
            "notable": 1,
            "quick_wins": 1,
            "worthwhile": 1,
            "body": [],
        }
        jsonschema.validate(doc, s)


# ---------------------------------------------------------------------------
# Schema rejects schema_version=1 (const violation)
# ---------------------------------------------------------------------------

class TestSchemaRejectsVersion1:
    """Documents with schema_version=1 must FAIL validation (const=2)."""

    @pytest.mark.parametrize("schema_file,doc_factory", [
        ("audit-report-v1.schema.json", lambda: {
            "schema_version": 1, "report_id": "x", "audit_target": "/x",
            "audit_timestamp": "2026-04-29T00:00:00Z", "tool_version": "2.0.3",
            "input_type": "code", "project_content_sha256": "a" * 64,
            "flags": [], "dimensions_activated": ["CORRECTNESS"],
            "subtree_grouping_applied": False, "token_cap_partial": False,
            "q_gate": {"pass_a": "pass", "pass_b": "pass"}, "findings": [],
        }),
    ])
    def test_schema_rejects_version_1(self, schema_file, doc_factory):
        s = load_schema(schema_file)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(doc_factory(), s)


# ---------------------------------------------------------------------------
# Dimension plugin frontmatter schema_version = 2
# ---------------------------------------------------------------------------

class TestDimensionPluginSchemaVersion:
    """Every dimension plugin must declare schema_version: 2 in frontmatter."""

    @pytest.mark.parametrize("plugin_file", DIMENSION_PLUGINS)
    def test_dimension_plugin_schema_version_is_2(self, plugin_file):
        plugin = load_dimension_plugin(plugin_file)
        assert plugin.get("schema_version") == 2, (
            f"{plugin_file} schema_version must be 2, got {plugin.get('schema_version')}"
        )


# ---------------------------------------------------------------------------
# Dimension plugin prompt_template declares {{input_type}}
# ---------------------------------------------------------------------------

class TestDimensionPluginPromptInputType:
    """Every dimension plugin prompt_template must reference {{input_type}}."""

    @pytest.mark.parametrize("plugin_file", DIMENSION_PLUGINS)
    def test_prompt_template_declares_input_type(self, plugin_file):
        plugin = load_dimension_plugin(plugin_file)
        prompt = plugin.get("prompt_template", "")
        assert "{{input_type}}" in prompt, (
            f"{plugin_file} prompt_template must contain {{{{input_type}}}} placeholder"
        )


# ---------------------------------------------------------------------------
# Schema version consistency with graph.json
# ---------------------------------------------------------------------------

def test_graph_json_version_is_2_0_3():
    with open(os.path.join(SKILL, "graph.json")) as f:
        g = json.load(f)
    assert g.get("version") == "2.0.3", f"graph.json version must be 2.0.3, got {g.get('version')}"
