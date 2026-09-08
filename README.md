# DailyPaper

Read the reports on the **[DailyPaper website](https://yaojianyu77.github.io/dailypaper/)**.

Change reports by editing **[DAILY_REPORT_PRODUCT_REQUIREMENTS.md](DAILY_REPORT_PRODUCT_REQUIREMENTS.md)**. The production pipeline and its Codex skills read this file on every run.

| Six settings | What to edit |
|---|---|
| [Research areas](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#1-research-areas) | Topics, priorities, exclusions |
| [Search sources](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#2-search-sources) | Eligible venues and publication types |
| [Time windows](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#3-time-windows) | Calendar windows, timezone, daily schedule |
| [Selection](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#4-selection) | Counts, ranking, shortfalls |
| [Per-paper content](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#5-per-paper-content) | Language, depth, visuals, model and Ultra policy |
| [Final research trends](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#6-final-research-trends) | Heading, count, evidence requirements |

Install or update from `main` on the always-on Linux host, with Python 3.11+, Node.js/npm, Git, a running Cronie service, the existing Codex login, and Git push access:

```bash
bash scripts/install_local_cron.sh
```

This updates Codex and Python dependencies, checks the authenticated runtime with a synthetic PDF, and installs or updates **one daily job at 07:00 America/New_York**. It preserves unrelated schedules, follows daylight saving time, and blocks overlapping runs. Setup does not generate a report. If Codex needs authentication, use `codex login` and rerun setup; approval settings remain intact.

```bash
bash scripts/install_local_cron.sh --status
bash scripts/install_local_cron.sh --logs
bash scripts/install_local_cron.sh --check  # live runtime check; no report/history writes
```

Each daily run refreshes official model recommendations, checks account access and exact Ultra support, and logs the resolved model and mode. Failure stops generation without a downgrade. Successful runs verify, archive, commit, and push through the existing runner; retries resume the same date. Keep the checkout clean. Existing reports deploy through the Pages workflow.

Maintainers: [execution rules](AGENTS.md) · [stage techniques](skills/) · [verified status and limitations](PROJECT_STATE.md) · [implementation and testing](docs/implementation.md). Older setup notes are [archived](docs/archive/README.md).
