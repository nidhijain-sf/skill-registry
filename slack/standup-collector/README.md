# Standup Collector

Sample Slackbot skill that shows the expected layout. Replace or delete it once real skills exist.

- `manifest.json` declares the bot user, slash command and the exact OAuth scopes. Reviewers compare these scopes with `skill.json` and the checklist in `docs/REVIEW_CHECKLIST.md`.
- Do not commit tokens or signing secrets. The bot reads them from the workspace secret store at runtime.

## Behaviour

1. At the configured time the bot sends each channel member a direct message asking for yesterday, today and blockers.
2. When everyone has replied, or at the cutoff time, it posts one combined summary in the channel.
