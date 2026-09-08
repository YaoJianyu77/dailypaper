# DailyPaper

Read daily research reports covering AI and computer science on the existing website. Change their requirements in one settings page.

**[Read the website](https://YaoJianyu77.github.io/dailypaper/)** · **[Edit daily-paper settings](https://github.com/YaoJianyu77/dailypaper/edit/main/DAILY_REPORT_PRODUCT_REQUIREMENTS.md)** · **[View the settings](DAILY_REPORT_PRODUCT_REQUIREMENTS.md)** · **[Run once](#run-once)**

The homepage previews the current report. The archive supports paper-title search and month filters; each daily article includes a paper directory, complete analyses, expandable figures, and links to adjacent reports.

## What do you want to change?

All six sections are in **Daily Paper Settings**. You do not need to search the scripts or skills for routine changes.

| I want to change… | Open this section |
|---|---|
| The research topics to include or exclude | [1. Research areas](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#1-research-areas) |
| The conferences, journals, and search sources | [2. Search sources](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#2-search-sources) |
| How recent the latest and classic papers should be | [3. Time windows](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#3-time-windows) |
| The daily paper count and non-repetition rules | [4. Selection](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#4-selection) |
| Summary language, length, structure, and visible figures/tables | [5. Per-paper content](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#5-per-paper-content) |
| The final cross-paper research-trend section | [6. Final research trends](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#6-final-research-trends) |

Open a section, edit the relevant value or text, and save it to `main`. Do not reset history when changing preferences.

## How the project fits together

**Server/Codex → read settings and skills → generate and validate the report → commit report and history → push to GitHub → static website.**

This is the intended production path, not a claim that unattended generation has been validated. ChatGPT is optional for discussion; it does not need to republish the website's report.

| Location | Purpose | Normally edited by |
|---|---|---|
| `DAILY_REPORT_PRODUCT_REQUIREMENTS.md` | Your six report settings | You |
| `AGENTS.md` and `skills/` | How an agent carries out those settings | Maintainer / Codex |
| `content/daily/` and `content/assets/papers/` | Reports and their visible images | Generator |
| `state/recommendation_history.json` | Permanent recommendation history | Generator |
| `scripts/` and existing helper directories | Implementation | Maintainer / Codex |

## Run once

In a Codex session with this repository checked out and authorized GitHub access, send:

> Read `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`, `PROJECT_STATE.md`, and `AGENTS.md` from the current `main` branch. Execute Systems Paper Daily once using the required repository skills. Prepare the complete report for the existing website, preserve permanent recommendation history, verify the report and rendered visuals, then commit and push only validated report, asset, and history changes. Resume an existing run for today's configured local date instead of choosing another set. Do not create a branch, install a timer, modify a scheduled task, or weaken the settings to accommodate legacy scripts. Stop and report the exact blocker if a required check fails.

This is a real integration test: successfully committed recommendations enter permanent history. It is not a promise that the legacy `scripts/run_local_daily.py` command already implements this workflow.

## Implementation status

The settings page is the **agent's instruction source**, not yet a configuration parser for the legacy Python runner. That runner still reads `config.yaml` and has conflicting older defaults. Editing the settings page does **not** silently update that runner or a server's timer. See [current implementation gaps](PROJECT_STATE.md).

For implementation work, start with [AGENTS.md](AGENTS.md). Superseded setup instructions and the old roadmap are in [the historical archive](docs/archive/README.md), not part of the current setup.

Website rendering uses `scripts/build_site.py`, `scripts/site_content.py`, and `scripts/site_assets/`. The Pages workflow builds directly from `content/daily/` and deploys on pushes to `main`; rendering preserves the source reports and recommendation history.
