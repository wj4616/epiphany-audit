#!/usr/bin/env python3
"""Checks every module file has all required Layer-B contract sections."""
import os, sys, glob, re

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED_SECTIONS = [
    "## Inputs", "## Outputs", "## Side Effects",
    "## Halt Conditions", "## Token Budget",
    "## Backtrack / Aggregation", "## Fan-out Cardinality",
    "## Back-edge Endpoints"
]

errors = []
module_files = sorted(glob.glob(os.path.join(SKILL, "modules/*.md")))
if not module_files:
    print("ERROR: no module files found")
    sys.exit(1)

for path in module_files:
    content = open(path).read()
    missing = [s for s in REQUIRED_SECTIONS
               if not re.search(rf'^{re.escape(s)}\s*$', content, re.MULTILINE)]
    if missing:
        errors.append(f"{os.path.basename(path)}: missing {missing}")

if errors:
    print("Module structure errors:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print(f"All {len(module_files)} modules have required sections. OK.")
