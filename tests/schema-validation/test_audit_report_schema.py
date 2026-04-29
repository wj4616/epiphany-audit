# tests/schema-validation/test_audit_report_schema.py
import json, os, pytest
import jsonschema

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_schema():
    with open(os.path.join(SKILL, "schemas/audit-report-v1.schema.json")) as f:
        return json.load(f)

def load_fixture(name):
    with open(os.path.join(SKILL, f"tests/schema-validation/fixtures/{name}.json")) as f:
        return json.load(f)

def test_valid_audit_report_passes():
    jsonschema.validate(load_fixture("valid_audit_report"), load_schema())

def test_missing_report_id_fails():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(load_fixture("invalid_audit_report_missing_id"), load_schema())

def test_bad_severity_fails():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(load_fixture("invalid_audit_report_bad_severity"), load_schema())

def test_dimensions_activated_must_contain_correctness():
    schema = load_schema()
    bad = load_fixture("valid_audit_report")
    bad["dimensions_activated"] = ["SECURITY"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_evidence_excerpt_extended_requires_high_confidence():
    schema = load_schema()
    bad = load_fixture("valid_audit_report")
    bad["findings"][0]["evidence_excerpt_extended"] = True
    bad["findings"][0]["confidence"] = "MEDIUM"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_critical_finding_requires_medium_or_high_confidence():
    schema = load_schema()
    bad = load_fixture("valid_audit_report")
    bad["findings"][0]["severity"] = "CRITICAL"
    bad["findings"][0]["confidence"] = "LOW"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
