<!-- Delta spec. Lives under a capability directory: specs/<capability>/spec.md
CLI mechanics: scenarios take exactly four hashtags - the parser silently
skips mis-levelled ones and they are lost at archive with no warning. A
MODIFIED block must copy the entire existing requirement, header text
included: archive replaces the whole block by matching that header, so a
partial copy silently drops what was left out. A brand-new capability opens
with "## Purpose" (>=50 chars) or the merged spec carries a TBD placeholder.
No behaviour change at all? Set skip_specs: true in the change's
.openspec.yaml instead of inventing a requirement. -->

## ADDED Requirements

### Requirement: <name>

The system MUST <observable, testable behavior>.

#### Scenario: <name>

- GIVEN <initial context>
- WHEN <action or event>
- THEN <expected, observable outcome>

## MODIFIED Requirements

<!-- A MODIFIED block replaces the whole requirement: repeat every surviving
scenario, including untouched ones. Note the previous behavior. -->

## REMOVED Requirements

<!-- State why removed and reference the migration/sunset plan. -->
