---
name: creating-skills
description: Scaffolds a new Antigravity skill directory under .agent/skills/. Use when the user asks to create a skill, build a skill, add a skill, or instantiate a skill for the agent.
---

# Creating Antigravity Skills

## When to use this skill
- User says "create a skill for X", "build me a skill", "add a skill", "make a skill"
- User wants to encode a repeatable workflow into the agent's permanent capability set
- User references `.agent/skills/` directly

## Checklist
- [ ] Determine skill name (gerund form, kebab-case, ≤64 chars)
- [ ] Draft `SKILL.md` with correct YAML frontmatter
- [ ] Decide which optional folders are needed (`scripts/`, `examples/`, `resources/`)
- [ ] Create files under `.agent/skills/<skill-name>/`
- [ ] Verify skill is usable by re-reading `SKILL.md` as if seeing it fresh

## Workflow

### 1. Name the skill
- Gerund form: `creating-skills`, `scraping-websites`, `managing-databases`
- Lowercase, hyphens only — no spaces, underscores, or special chars
- No "claude", "anthropic", or "antigravity" in the name

### 2. Write SKILL.md

```markdown
---
name: <gerund-name>
description: <third-person, ≤1024 chars. Include trigger keywords.>
---

# <Skill Title>

## When to use this skill
- <Trigger phrase 1>
- <Trigger phrase 2>

## Checklist
- [ ] Step A
- [ ] Step B

## Instructions
<Specific rules, heuristics, or code>

## Resources
- [scripts/foo.py](scripts/foo.py)
```

Keep `SKILL.md` under **500 lines**. Offload detail to `scripts/` or `resources/` and link with relative paths using forward slashes.

### 3. Choose optional folders

| Folder | When to add |
|---|---|
| `scripts/` | Repeatable CLI operations (argparse, dotenv, exit codes 0/1/2) |
| `examples/` | Reference implementations or sample inputs/outputs |
| `resources/` | Templates, prompt snippets, config files |

### 4. Writing rules
- **High freedom** (heuristics) → bullet points
- **Medium freedom** (templates) → fenced code blocks
- **Low freedom** (fragile ops) → exact bash/powershell commands
- Never use `\` for paths — always `/`
- Don't over-explain basics; assume a capable agent

### 5. Validation loop
Before declaring the skill done:
1. Re-read `SKILL.md` cold — does it unambiguously tell the agent what to do?  
2. Check frontmatter parses cleanly (valid YAML, name/description present)  
3. If scripts exist, confirm they have `--help` and can self-test
