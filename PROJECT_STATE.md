# Implementation Status

Maintainer reference, not another settings page. For routine use, open [README.md](README.md); to change report requirements, edit [Daily Paper Settings](DAILY_REPORT_PRODUCT_REQUIREMENTS.md).

## Intended product

Server/Codex generation → GitHub `main` → existing static website. Reports and figures stay in the existing `content/` layout, and permanent exclusions stay in `state/recommendation_history.json`. ChatGPT is optional for discussion, not a required content-delivery hop.

This describes the requested architecture. It does not certify the current server, timer, or unattended generation.

## Verified repository boundary

The documentation cleanup inspected the repository based on commit `8e1c31550f1b394da91f7867d3ffd495bdd0629a`. It reorganizes instructions without changing runtime code, data, server configuration, or scheduled tasks.

| Component | Current evidence / remaining gap |
|---|---|
| User settings | One six-section page at `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`, linked directly from README. Agents must read it each run. |
| Legacy runner | `scripts/run_local_daily.py` exists. Its established search/enrich/publish path must not be advertised as a verified implementation of the full-paper product. |
| Legacy configuration | `config.yaml` still contains 2 fresh + 2 established + 1 classic quotas, day-based windows, and recommendation cooldowns. These conflict with current user settings. This cleanup does not synchronize them. |
| Legacy analysis | `config.yaml` still describes short enrichment, with abstract context limits. A full-paper skill alone does not make an abstract-only input complete. |
| History | Legacy helpers use `state/paper_index.json`; agent instructions require `state/recommendation_history.json`. Production writers still need a verified common history contract. Neither file was edited or reset in this cleanup. |
| Website | Existing content is built with `scripts/build_site.py` and deployed through `.github/workflows/pages.yml`. No site build or deployment verification was performed by the documentation cleanup. |
| Scheduling | A local cron helper exists, and previous discussions covered ChatGPT scheduling. Neither a currently installed server timer nor unattended runtime permissions were checked here. |

## Maintenance rule

Before calling the server production-ready, wire the generator to the authoritative settings, eliminate conflicting selection/history behavior, and verify a full end-to-end run with rendered visuals and safe retries. Do not ask the user to synchronize several configuration files by hand or claim that editing Markdown has changed code that never reads it.

Keep useful legacy helper paths in place until their imports, subprocess calls, tests, and deployment references can be updated together. Obsolete quickstart instructions and the old roadmap have been moved to `docs/archive/`; they are not the current setup procedure.

An old saved task may still reference this file and `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`; both paths remain valid. This cleanup does not modify that task or its execution time.
