# Review checklist

For reviewers. Approve only when every applicable box can be ticked. Merge means approved.

## Every skill

- [ ] The description says what the skill does and when to use it.
- [ ] A named team owns it, and the contact channel is real.
- [ ] No secrets, tokens, customer data or real personal data anywhere in the folder.
- [ ] The example output in the PR matches what the description promises.
- [ ] It does not tell the model to ignore its instructions, hide actions from the user or send data somewhere unexpected.
- [ ] It does not duplicate an existing skill. If it does, ask the author to extend that one.

## Claude Code

- [ ] `allowed-tools` lists only what the skill needs. Unrestricted `Bash` needs a written reason.
- [ ] Any `scripts/`, hooks or `.mcp.json` were read line by line by the security group.
- [ ] Network calls go only to hosts named in the PR description.

## Gemini

- [ ] The context file asks only for the file or document access it needs.
- [ ] No instruction to fetch or post data outside the user's session.

## Slackbot

- [ ] Every scope in `manifest.json` is used. Remove scopes the bot does not need.
- [ ] It reads only channels the user invited it to. Reading private channels or DMs needs security approval.
- [ ] Messages it posts do not include data the channel members could not already see.
- [ ] Secrets come from the secret store, not from files in this repo.

## Tier decision

- **Community:** passes the automated checks and one reviewer. Listed with a Community badge.
- **Certified:** also reviewed by the security group, has an owner on call, and a reviewed date within the last 12 months.

## Updates and removal

- Any change to scripts, hooks, MCP config, tool permissions or Slack scopes is reviewed as a new submission.
- To retire a skill, set `status` to `deprecated`. If it is unsafe, set it to `revoked`, which removes it from the catalog and the marketplace on the next build.
