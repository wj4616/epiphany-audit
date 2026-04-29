# Audio Plugin Preset System — Design Specification

## Overview
A cross-platform preset management system for VST3/AU plugins.

## Requirements

### REQ-001: Preset Loading
The system shall load preset files in `.fxp` and `.vstpreset` formats.

### REQ-002: Preset Saving
The system shall save current parameter state to a preset file.

### REQ-003: Preset Browser
The system shall provide a browsable preset library with search and categorization.

### REQ-004: Factory Presets
The system shall include a read-only factory preset bank that cannot be overwritten.

## Acceptance Criteria

### AC-001: Load Performance
Preset loading shall complete within 50ms for presets up to 500 parameters.

### AC-002: Cross-DAW Compatibility
Presets saved on one DAW shall load identically on another DAW running the same plugin version.
