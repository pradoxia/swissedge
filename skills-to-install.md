# Skills to Install in Claude Code

## Before You Start

Open Claude Code and install these skills. Only install what you need for the current phase.

## Phase 0-1: Essential Skills (install now)

### From Anthropic Official (anthropics/skills)
These are built-in or easily installable:
- **frontend-design** — for the web dashboard and research journal
- **pdf** — for generating PDF reports of investment analyses

### From Community Repositories

**Investment / Special Situations:**
```bash
# Behavioral Value Investor's Special Situations Screener
# Download from: https://behavioralvalueinvestor.substack.com/p/ai-for-serious-investors-1-the-special
# Install: Settings → Skills → Upload the .skill file

# lyndonkl/claude — financial analysis skills
# Contains: special-situations-analyst, special-situations-valuation, financial-statement-analyzer
/plugin marketplace add lyndonkl/claude
/plugin install special-situations-valuation
```

**Trading / Screening:**
```bash
# tradermonty/claude-trading-skills
# Contains: finviz-screener, portfolio-manager, thesis-tracker
/plugin marketplace add tradermonty/claude-trading-skills
/plugin install finviz-screener
```

### Custom Skill: SwissEdge Doctor
Create this yourself in `~/.claude/skills/swissedge-doctor/SKILL.md`:

```markdown
---
name: swissedge-doctor
description: Run system health diagnostics for the SwissEdge platform. Use when the user says "revisa el sistema", "check health", "doctor", or asks about system status. Runs scripts/doctor.py and interprets the results.
---

# SwissEdge Doctor Skill

When the user asks to check the system health:

1. Run `python scripts/doctor.py` from the project root
2. Read the output carefully
3. For each component with status "error" or "warning":
   - Explain what the component does
   - Explain why it might be failing
   - Suggest specific fix steps
4. For OpenClaw-related failures:
   - Check if the cron job is configured correctly
   - Check if the endpoint URL is correct
   - Suggest checking OpenClaw logs
5. Summarize: what works, what's broken, what's degraded
6. Prioritize fixes by impact: critical first, then warnings

## Common Issues and Fixes

- **PostgreSQL connection failed**: Check if Docker container is running (`docker ps`)
- **Tutti.ch scraper blocked**: Likely rate limited or User-Agent blocked. Suggest waiting or switching to manual mode.
- **SEC EDGAR timeout**: Check if User-Agent header includes email. SEC requires this.
- **OpenClaw cron stale**: Check OpenClaw dashboard for task status. May need restart.
- **Telegram webhook missing**: Bot token may have changed. Reconfigure.
```

## Phase 2: Additional Skills (install later)

```bash
# For web development
# anthropics/skills frontend-design is already installed

# For more marketplace adapters
# No specific skill needed — we build custom adapters

# For more investment sources
/plugin install thesis-tracker  # from tradermonty
```

## Phase 3: Web & Publishing Skills (install even later)

```bash
# For SEO and content
# Consider: content-creator skills from alirezarezvani/claude-skills
/plugin marketplace add alirezarezvani/claude-skills
/plugin install content-creator
```

## Skills NOT to Install

Don't install these — they add context without value for this project:

- Generic code review skills (Claude Code already does this)
- Git commit message generators (overkill for a solo project)
- Language-specific skills for languages you're not using (Ruby, Go, Rust, etc.)
- Multiple competing investment skills (pick one set and stick with it)
- Dozens of "awesome" skills from curated lists — only install what you'll use THIS WEEK

## Total Skills Budget

| Phase | Skills installed | Estimated metadata tokens |
|-------|-----------------|--------------------------|
| 0-1   | 5-6             | ~600 tokens/session       |
| 2     | 7-8             | ~800 tokens/session       |
| 3     | 9-10            | ~1000 tokens/session      |

This is negligible. The important thing is not installing 50 skills "just in case".
