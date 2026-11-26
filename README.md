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
claude plugin marketplace add YOUR-ORG/skill-registry
```

Then inside Claude Code: `/plugin install <id>@team-skills`

Gemini and Slackbot skills show their install steps on the catalog page.

## Submitting a skill

See [CONTRIBUTING.md](CONTRIBUTING.md). Reviewers use [docs/REVIEW_CHECKLIST.md](docs/REVIEW_CHECKLIST.md).

## Set-up for the registry owners

1. Create the repo and push this folder to it.
2. Replace `YOUR-ORG` in `.github/CODEOWNERS` and create the teams it names.
3. Turn on branch protection for `main`: require pull requests, require the `Validate submission` check, and require review from Code Owners.
4. Host the catalog page. `publish.yml` builds `site/index.html` on every merge. Put it behind company SSO.
5. Delete the three sample skills once real ones are added.

## Things that are placeholders

- The Gemini install command and the `/skillbot enable` command on the catalog page are examples. Replace them in `site/template.html` with your real install steps.
- `catalog/queue.json` feeds the "In review" tab. It ships empty. A small CI job can fill it from open pull requests later.
- Install counts are not tracked, so the page leaves them out.
