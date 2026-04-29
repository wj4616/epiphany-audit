# Smoke Test 08 — Dimension Plugin Loading

**Setup:**
- A valid custom dimension plugin exists at `tests/smoke/fixtures/user-dimensions/test-custom-dim.md`
- Copy it to `~/.config/epiphany-audit/dimensions/test-custom-dim.md`

**Actions:**
1. Invoke `/epiphany-audit --audit` on a project that matches the plugin's activation triggers

**Expected outcomes:**
- N02 loads bundled plugins (5) + user plugin (1)
- User plugin appears in `dimensions_activated` if its triggers fire
- Structured event log shows `test-custom-dim: loaded`
- Findings from the plugin carry `provenance.plugin_name: test-custom-dim`
