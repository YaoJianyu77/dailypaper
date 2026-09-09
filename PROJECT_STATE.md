# Project status

[README](README.md) is the entry page. [Settings](DAILY_REPORT_PRODUCT_REQUIREMENTS.md) own preferences, [AGENTS.md](AGENTS.md) owns execution rules, and [implementation notes](docs/implementation.md) explain modules and recovery.

## Verified behavior

- The production runner reads the six settings, uses verified Codex research stages and linked skills, and checks complete permanent history. Publication archives the report, visuals, and history under one stable run ID; retries retain the original selection.
- The installed daily job was verified at 07:00 America/New_York, including reinstall idempotency, DST, timezone preservation, and overlapping-run exclusion. Runtime checks proved full-PDF reading, page rendering, image inspection, web search, skill routing, and a native subagent. Effective parent/child approvals were `never`, with unchanged workspace sandbox and denied external writes/network connections.
- The approved September 8 article contains four latest papers, seven figures, and one table; the missing classic slot is explained. Publication preserved prior history/evidence. Its shared-reader deployment is [21272aa / Pages run 34299457728](https://github.com/YaoJianyu77/dailypaper/actions/runs/34299457728), verified live at desktop/mobile widths with date selection, figure controls, and old-link redirects.
- The cleanup passed 84 isolated tests, covering complete Codex inputs, settings/skill edits, review routing, retry recovery, permanent exclusions, permissions, scheduling, and browser rendering. A focused end-to-end test also verifies that final review receives the complete article once, with paper-review receipts and browser evidence intact. Five canonical skills validate and remain discoverable through links; their retained image helper passes an isolated PDF extraction check.
- Skills own techniques; stage prompts retain field meanings and controller handoffs. Final review loads editing/visual skills and reuses paper-review receipts. Removing duplicate instructions and analysis copies reduced final-review text by about 34% when measured with the archived September 8 bundle; this measurement made no model call.
- All 53 reports and 58 image references remain intact. Production content, history, settings, runtime safeguards, and the daily schedule match their pre-cleanup hashes. No production recommendations were generated or published during cleanup.

## Remaining limitations

- Official model/effort guidance, account quota, runtime protocol changes, unavailable publishers, and service rate limits can stop a run. Unsupported or ambiguous model/effort choices never downgrade silently. A conflicting native child may start before its notification arrives; its output is rejected before acceptance.
- Discovery uses configured venue indexes and verified native web search, not an exhaustive proceedings crawl. Coverage and ambiguous publication dates can leave slots unfilled.
- Full-paper acquisition requires extractable text on every page and accessible relevant appendices within document limits. Scanned pages needing OCR and unavailable source versions stop preparation; there is no abstract fallback.
- Scientific correctness, topic fit, renamed-work relationships, and visual fidelity also require model review. Deterministic identity/hash/format checks do not prove those judgments.
- Interrupted reservations need their original preparation cache and compatible settings/runtime receipts. Preserve and reconcile them; neither reservations nor historical exclusions expire.
- The shared reader requires JavaScript. A local build or Git push alone does not prove deployment; verify the corresponding Pages run and live article.
