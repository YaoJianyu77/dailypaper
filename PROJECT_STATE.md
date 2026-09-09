# Project status

[README](README.md) is the entry page. [Settings](DAILY_REPORT_PRODUCT_REQUIREMENTS.md) own preferences, [AGENTS.md](AGENTS.md) owns execution rules, and [implementation notes](docs/implementation.md) explain modules and recovery.

## Verified behavior

- The production runner reads the six settings, uses verified Codex research stages and linked skills, and checks complete permanent history. Publication archives the report, visuals, and history under one stable run ID; retries retain the original selection.
- The installed daily job was verified at 07:00 America/New_York, including reinstall idempotency, DST, timezone preservation, and overlapping-run exclusion. Runtime checks proved full-PDF reading, page rendering, image inspection, web search, skill routing, and a native subagent. Effective parent/child approvals were `never`, with unchanged workspace sandbox and denied external writes/network connections.
- The approved September 8 article contains four latest papers, seven figures, and one table; the missing classic slot is explained. Publication preserved prior history/evidence. Its shared-reader deployment is [21272aa / Pages run 34299457728](https://github.com/YaoJianyu77/dailypaper/actions/runs/34299457728), verified live at desktop/mobile widths with date selection, figure controls, and old-link redirects.
- The cleanup passed 82 isolated tests, including complete Codex inputs, rejected retired API options, settings-only changes, retry recovery, permanent exclusions, permissions, scheduling, and browser rendering. Five skills validate and remain discoverable; their retained image helper passes an isolated PDF extraction check.
- All 53 reports and 58 image references remain intact. All 1,145 protected file/cron hashes match the baseline, and all 1,060 website output files are byte-identical to the deployed build. No production recommendations or history were changed during cleanup. Stage instruction payloads are 17–23% smaller; the six settings are unchanged.

## Remaining limitations

- Official model/effort guidance, account quota, runtime protocol changes, unavailable publishers, and service rate limits can stop a run. Unsupported or ambiguous model/effort choices never downgrade silently. A conflicting native child may start before its notification arrives; its output is rejected before acceptance.
- Discovery uses configured venue indexes and verified native web search, not an exhaustive proceedings crawl. Coverage and ambiguous publication dates can leave slots unfilled.
- Full-paper acquisition requires extractable text on every page and accessible relevant appendices within document limits. Scanned pages needing OCR and unavailable source versions stop preparation; there is no abstract fallback.
- Scientific correctness, topic fit, renamed-work relationships, and visual fidelity also require model review. Deterministic identity/hash/format checks do not prove those judgments.
- Interrupted reservations need their original preparation cache and compatible settings/runtime receipts. Preserve and reconcile them; neither reservations nor historical exclusions expire.
- The shared reader requires JavaScript. A local build or Git push alone does not prove deployment; verify the corresponding Pages run and live article.
