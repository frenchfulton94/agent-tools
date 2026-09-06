## Problem

<!-- The problem, from the user's perspective. -->

## Solution

<!-- The solution, from the user's perspective. -->

## User Stories

<!-- A long numbered list covering the behaviour this change ADDS. The specs
     artifact turns each story into requirements, so write these at length. -->

1. As a <actor>, I want <feature>, so that <benefit>

## Capabilities

<!-- Adding a surface to a capability that already exists? Say which way it goes
     and why: requirements on the existing capability when the surface is how that
     capability is reached, or a nested <existing>/ui when the surface has its own
     lifecycle and would otherwise swamp its parent. -->

### New Capabilities
<!-- Each becomes specs/<capability-path>/spec.md. Kebab-case the segments you
     introduce; follow the project's existing spec layout. -->
- `<capability-path>`: <what this capability covers>

### Modified Capabilities
<!-- Existing capabilities whose requirements change or are removed. Name which
     requirement moves and what about it changes — that line is what the delta
     edits against. Use the exact existing path
     under openspec/specs/. Leave empty when only the implementation changes; a
     change with no capabilities at all sets skip_specs: true in .openspec.yaml. -->
- `<existing-capability-path>`: <which requirement is changing>

## Out of Scope

<!-- What this change deliberately does not do. -->

## Impact

<!-- Affected code, APIs, dependencies, systems. Name any ADR this contradicts
     and make the case for reopening it. -->
