# DailyPaper

Read the **[website](https://yaojianyu77.github.io/dailypaper/)** or choose a date in the [report reader](https://yaojianyu77.github.io/dailypaper/reader/). One shared HTML page displays the daily Markdown; article text stays in `content/daily/`.

Edit **[DAILY_REPORT_PRODUCT_REQUIREMENTS.md](DAILY_REPORT_PRODUCT_REQUIREMENTS.md)** to change the next report. It is the only user settings file.

| Six settings | Controls |
|---|---|
| [Research areas](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#1-research-areas) | Topics, priorities, exclusions |
| [Search sources](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#2-search-sources) | Venues and publication types |
| [Time windows](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#3-time-windows) | Date windows, timezone, schedule |
| [Selection](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#4-selection) | Counts, ranking, shortfalls |
| [Per-paper content](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#5-per-paper-content) | Language, depth, visuals, model and reasoning |
| [Final research trends](DAILY_REPORT_PRODUCT_REQUIREMENTS.md#6-final-research-trends) | Heading, count, supporting evidence |

Install or update from a clean `main` checkout on the always-on Linux host:

```bash
bash scripts/install_local_cron.sh
```

Requires Python 3.11+, Node.js/npm, Git, a running Cronie service, an authenticated Codex account, and Git push access. Setup updates dependencies, verifies the runtime, and manages one **07:00 America/New_York** job with an overlap lock. It preserves unrelated schedules and does not generate a report.

```bash
bash scripts/install_local_cron.sh --status
bash scripts/install_local_cron.sh --logs
bash scripts/install_local_cron.sh --check   # live capability check
.cache/dailypaper/venv/bin/python scripts/run_local_daily.py --dry-run
.cache/dailypaper/venv/bin/python scripts/run_local_daily.py
```

The dry-run prepares and checks an article in temporary storage. The normal run verifies the current recommended model and strongest supported reasoning, generates the report, commits, and pushes. Unverified capabilities stop the run without a downgrade. GitHub Pages deploys the committed content.

Maintainers: [execution rules](AGENTS.md) · [skills](skills/) · [current status](PROJECT_STATE.md) · [implementation and tests](docs/implementation.md).
