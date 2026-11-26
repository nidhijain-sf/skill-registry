# Submitting a skill

## Easiest: the Submit a skill button

For skills that are instructions only (no scripts, hooks or MCP servers):

1. Open the catalog page and click **Submit a skill**. It opens a form on GitHub.
2. Fill it in and submit. You need a GitHub account with access to this repo.
3. A workflow turns your answers into the skill files and opens a pull request. It comments on your submission with the link, or lists what to fix.
4. A reviewer approves and merges. The skill then appears on the catalog.

Skills that need scripts, hooks or MCP servers go through a pull request, as below, so the security group can read the code.

## By pull request

1. **Create a folder** under the platform you build for. The folder name is the skill id: lowercase letters, numbers and hyphens.

   | Platform | Folder | Required files |
   |---|---|---|
   | Claude Code | `claude/<id>/` | `skill.json`, `.claude-plugin/plugin.json`, `skills/<id>/SKILL.md` |
   | Gemini | `gemini/<id>/` | `skill.json`, `gemini-extension.json`, `GEMINI.md` |
   | Slackbot | `slack/<id>/` | `skill.json`, `manifest.json`, `README.md` |

   Copy one of the sample skills as a starting point.

2. **Fill in `skill.json`.** This is what the catalog page shows.

   | Field | Meaning |
   |---|---|
   | `id`, `name`, `platform` | `id` must equal the folder name. `platform` is `claude`, `gemini` or `slack`. |
   | `category`, `tags`, `description` | How people find it. Say when to use it. Keep the description under 300 characters. |
   | `tier` | `community` for a normal submission. `certified` is granted by the security group, so submit as `community` first. |
   | `status` | `approved`. Reviewers change it to `deprecated` or `revoked` when needed. |
   | `version` | Semantic version, such as `1.0.0`. Bump it on every change. |
   | `owner`, `owner_contact` | The team that maintains it and where to reach them. |
   | `reviewed` | Date of the last review, such as `2026-11-26`. |
   | `tools` | What it can access: tools for Claude Code, file access for Gemini, Slack scopes for Slackbot. |

3. **Run the checks locally.**

   ```bash
   python scripts/validate.py
   python scripts/build_catalog.py
   ```

   `validate.py` must report no errors. `build_catalog.py` regenerates `catalog/catalog.json` and `.claude-plugin/marketplace.json`. Commit both.

4. **Open a pull request** and fill in the template. CI runs the same checks. CODEOWNERS then asks the right reviewers. Anything with scripts, hooks, MCP servers or Slack manifests also goes to the security group.

5. **Merge is approval.** After merge the catalog page and the Claude Code marketplace update.

## Updating or retiring

- Open a pull request that changes the files and bumps `version`.
- To retire a skill, set `status` to `deprecated` and say what replaces it in the PR.
