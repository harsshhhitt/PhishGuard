---
description: Create a new .agent/skills/ entry from a description of what the skill should do
inputs:
  - name: skill description
    description: What the skill should automate or teach the agent
outputs:
  - name: .agent/skills/<skill-name>/SKILL.md
    description: The new skill directory with a conformant SKILL.md
skill: .agent/skills/creating-skills/SKILL.md
---

## Goal
Turn a plain-English description of a capability into a properly formatted `.agent/skills/` entry that the agent can load and use immediately.

## Steps
1. Read `.agent/skills/creating-skills/SKILL.md` for the full checklist and writing rules.
2. Determine the skill name (gerund, kebab-case).
3. Draft `SKILL.md` following the template in the skill.
4. Decide if `scripts/`, `examples/`, or `resources/` sub-folders are needed.
5. Create the files under `.agent/skills/<skill-name>/`.
6. Re-read `SKILL.md` cold to validate clarity.

## Edge cases & notes
- Keep `SKILL.md` under 500 lines; offload to sub-folders and link with relative paths.
- Always use `/` for paths (Windows paths with `\` break portability).
- If the user gives you an existing markdown doc (like `execution/skill_creator.md`), treat it as the source spec and derive the skill from it.
