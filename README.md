# Skill Registry

One place where the team registers, reviews and installs skills for Claude Code, Gemini and Slackbot. A skill is listed only after a reviewer approves the pull request that adds it.

```
Author -> pull request -> automated checks -> human review (CODEOWNERS) -> merge = approved -> published
```

## Layout

```
claude/<id>/      Claude Code plugins (installed from the marketplace)
gemini/<id>/      Gemini extensions
slack/<id>/       Slackbot skills
catalog/          generated catalog.json, optional queue.json
scripts/          validate.py (CI gate), build_catalog.py (generator)
site/             template.html for the catalog page (index.html is generated)
docs/             reviewer checklist
.github/          CODEOWNERS, PR template, CI workflows
```

## Installing a skill

Claude Code, once per machine:

```bash
claude plugin marketplace add nidhijain-sf/skill-registry
```

Then inside Claude Code: `/plugin install <id>@team-skills`

Gemini and Slackbot skills show their install steps on the catalog page.

## Submitting a skill

See [CONTRIBUTING.md](CONTRIBUTING.md). Reviewers use [docs/REVIEW_CHECKLIST.md](docs/REVIEW_CHECKLIST.md).

## Set-up for the registry owners

1. Create the repo and push this folder to it.
2. **Turn on the approval rule.** In the repo go to Settings, Rules, Rulesets, New ruleset, Import a ruleset, and choose `.github/rulesets/protect-main.json`. It requires a pull request, one approval from a Code Owner, and a passing `validate` check before anything merges to `main`. Admins can bypass it, so the owner can merge their own pull requests. Do not skip this step: CODEOWNERS alone does not block merges.
3. In Settings, Actions, General, set "Fork pull request workflows from outside collaborators" to require approval, so CI does not run for strangers' pull requests until you allow it.
4. Host the catalog page. `publish.yml` builds `site/index.html` only when something merges to `main`, so nothing appears on the page without approval. Put it behind company SSO when the repo is private.
5. Delete the three sample skills once real ones are added.

## Moving to a reviewer team

1. Create the teams in your GitHub org and move the repo there.
2. In `.github/CODEOWNERS`, replace `@nidhijain-sf` on each line with the right team. Use separate teams per platform and a security team for the scripts and manifest lines.
3. Re-import the ruleset in the new repo. If you want more than one approval, raise `required_approving_review_count` in `.github/rulesets/protect-main.json` first.

## Things that are placeholders

- The Gemini install command and the `/skillbot enable` command on the catalog page are examples. Replace them in `site/template.html` with your real install steps.
- `catalog/queue.json` feeds the "In review" tab. It ships empty. A small CI job can fill it from open pull requests later.
- Install counts are not tracked, so the page leaves them out.
