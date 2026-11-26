---
name: release-notes-writer
description: Write customer-facing release notes from a list of merged pull requests or work item titles. Use when the user asks for release notes, a changelog entry or "what shipped".
allowed-tools: Read, Grep
---

# Release Notes Writer

Sample skill that shows the expected layout. Replace or delete it once real skills exist.

## Steps

1. Ask for the list of merged pull requests or work item titles if none was provided.
2. Group items by feature area. Put breaking changes in their own section at the top.
3. Rewrite each item as one plain sentence that says what changed for the customer, not how it was built.
4. Leave out internal-only items such as refactors and test changes unless the user asks for them.

## Output

A Markdown document with a heading per feature area and one bullet per change.
