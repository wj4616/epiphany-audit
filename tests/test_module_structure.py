import os, glob, re, pytest

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED_SECTIONS = [
    "## Inputs", "## Outputs", "## Side Effects",
    "## Halt Conditions", "## Token Budget",
    "## Backtrack / Aggregation", "## Fan-out Cardinality",
    "## Back-edge Endpoints",
]
MODULE_FILES = sorted(glob.glob(os.path.join(SKILL, "modules/*.md")))


def pytest_collection_modifyitems(items):
    pass


EXPECTED_NODE_COUNT = 29


def test_node_count():
    """v2.0.0: 29 modules (27 v1.x + N00a + N00b)."""
    assert len(MODULE_FILES) == EXPECTED_NODE_COUNT, (
        f"expected {EXPECTED_NODE_COUNT} module files, found {len(MODULE_FILES)}"
    )


@pytest.mark.parametrize("path", MODULE_FILES)
def test_module_has_required_sections(path):
    content = open(path).read()
    missing = [
        s for s in REQUIRED_SECTIONS
        if not re.search(rf"^{re.escape(s)}\s*$", content, re.MULTILINE)
    ]
    assert not missing, f"{os.path.basename(path)}: missing {missing}"
