# DailyPaper

Read the reports on the **[DailyPaper website](https://yaojianyu77.github.io/dailypaper/)**.

Change reports by editing **[DAILY_REPORT_PRODUCT_REQUIREMENTS.md](DAILY_REPORT_PRODUCT_REQUIREMENTS.md)**. The generation pipeline and its Codex/API prompts read this file on every run.

| Six settings | What to edit |
|---|---|
| [Research areas](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#1-research-areas) | Topics, priorities, exclusions |
| [Search sources](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#2-search-sources) | Eligible venues and publication types |
| [Time windows](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#3-time-windows) | Calendar windows and timezone |
| [Selection](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#4-selection) | Counts, ranking, shortfalls |
| [Per-paper content](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#5-per-paper-content) | Language, depth, structure, figures and tables |
| [Final research trends](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#6-final-research-trends) | Heading, count, evidence requirements |

From a clean checkout of `main`, with the existing Codex login and Git push access:

```bash
uv run --with-requirements requirements.txt python scripts/run_local_daily.py
```

The command prepares full-paper analyses, verifies the rendered article, archives the report and permanent history, commits, and pushes. A retry resumes or verifies the same date's run. Add `--dry-run` to prepare and check in temporary storage without publishing or changing production history; it still uses network/model access. `--skip-push` archives and commits locally.

The manual **Daily Papers** GitHub Action uses the same runner with GitHub Models. Neither command installs or changes a schedule. YAML contains only infrastructure settings such as model transport, service limits, and site paths.

Maintainers: [execution rules](AGENTS.md) · [stage techniques](skills/) · [verified status and limitations](PROJECT_STATE.md) · [implementation and testing](docs/implementation.md). Older setup notes are [archived](docs/archive/README.md).
