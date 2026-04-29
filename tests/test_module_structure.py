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


@pytest.mark.parametrize("path", MODULE_FILES)
def test_module_has_required_sections(path):
    content = open(path).read()
    missing = [
        s for s in REQUIRED_SECTIONS
        if not re.search(rf"^{re.escape(s)}\s*$", content, re.MULTILINE)
    ]
    assert not missing, f"{os.path.basename(path)}: missing {missing}"
