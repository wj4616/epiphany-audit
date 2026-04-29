# Dimension Plugins

Each `.md` file in this directory is a dimension plugin conforming to
`schemas/dimension-plugin-v1.schema.json`.

## Built-in plugins (versioned with the skill)

| File               | Dimension     | Floor? |
|--------------------|---------------|--------|
| correctness.md     | CORRECTNESS   | yes — always activated; cannot be shadowed |
| maintainability.md | MAINTAINABILITY | yes — always activated; cannot be shadowed |
| architecture.md    | ARCHITECTURE  | no |
| performance.md     | PERFORMANCE   | no |
| security.md        | SECURITY      | no |

## Adding a custom dimension

1. Create `~/.config/epiphany-audit/dimensions/<your-dimension>.md`
2. Populate YAML frontmatter per `dimension-plugin-v1.schema.json`
3. A plugin with the same `name` as a built-in shadows the built-in entirely
   (exception: CORRECTNESS and MAINTAINABILITY cannot be shadowed)
4. Plugin files that fail schema validation are logged and skipped — they do not
   halt the audit

## Example custom plugin frontmatter

~~~yaml
schema_version: 1
name: juce-rt-safety
display_name: JUCE Real-Time Audio Safety
version: 1.0.0
applies_to:
  languages: [cpp]
  project_markers: ["CMakeLists.txt", "*.vst3"]
activation_triggers:
  - type: file_present
    path: "**/JuceHeader.h"
prompt_template: |
  Analyze for allocations and mutex locks on the audio thread...
kb_route_query: null
intra_node_token_budget: 30000
priority: high
~~~
