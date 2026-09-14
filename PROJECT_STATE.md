# Project status

[README](README.md) is the entry page. [Settings](DAILY_REPORT_PRODUCT_REQUIREMENTS.md) own preferences, [AGENTS.md](AGENTS.md) owns execution rules, and [implementation notes](docs/implementation.md) explain modules and recovery.

## Verified behavior

- The production runner reads the six settings, uses verified Codex research stages and linked skills, and checks complete permanent history. Publication archives the report, visuals, and history under one stable run ID; retries retain the original selection.
- The installed daily job was verified at 07:00 America/New_York, including reinstall idempotency, DST, timezone preservation, and overlapping-run exclusion. Runtime safeguards cover full-PDF reading, page rendering, image inspection, web search, skill routing, explicit `approvalPolicy=never`, the unchanged workspace sandbox, and denied external writes/network connections.
- The approved September 8 article contains four latest papers, seven figures, and one table; the missing classic slot is explained. Publication preserved prior history/evidence. Its shared-reader deployment is [21272aa / Pages run 34299457728](https://github.com/YaoJianyu77/dailypaper/actions/runs/34299457728), verified live at desktop/mobile widths with date selection, figure controls, and old-link redirects.
- The suite passes 86 isolated tests, covering complete Codex inputs, settings/skill edits, the model-call budget, retry recovery, permanent exclusions, permissions, scheduling, and browser rendering. A five-paper fixture uses selection, five one-pass analyses, and one trend synthesis, with no paper/report model reviews. Fresh structural failures stop after one analysis call; an explicit local date can resume an unfinished report after midnight. Five canonical skills validate and remain discoverable through links; their retained image helper passes an isolated PDF extraction check.
- The September 13 production audit found 46.21 million raw tokens for the main run plus recovery, of which 40.62 million were cached input. The Codex weekly meter moved from 33% to 53%; including earlier report attempts, report-related jobs accounted for about 23 percentage points. Paper/report reviews consumed about 16.2 million tokens and delegated children another 16.2 million. The configured workflow now uses balanced `medium` reasoning, rejects delegation, removes both review stages and the daily synthetic diagnostic, records per-call token receipts, and keeps deterministic evidence/rendering validation.
- All 54 reports remain intact. The September 13 report is archived at commit `deb27cb22bd30faa164eee1263116e96323b09aa`; its Pages deployment and live desktop/mobile article were verified.

## Remaining limitations

- Official model/effort guidance, account quota, runtime protocol changes, unavailable publishers, and service rate limits can stop a run. Unsupported model/effort choices never downgrade silently. Any subagent or collaboration-agent activity stops the stage.
- Discovery uses configured venue indexes and verified native web search, not an exhaustive proceedings crawl. Coverage and ambiguous publication dates can leave slots unfilled.
- Full-paper acquisition requires extractable text on every page and accessible relevant appendices within document limits. Scanned pages needing OCR and unavailable source versions stop preparation; there is no abstract fallback.
- Each paper now receives one model analysis without an independent model reviewer. Deterministic identity, source, page, hash, structure, visual, and browser checks do not independently prove every scientific judgment. This is the explicit quality/cost trade-off of the token-efficient workflow.
- Production token reduction has not yet been measured on a new report. Per-call receipts will make the first lean scheduled run directly comparable with the September 13 baseline.
- Interrupted reservations need their original preparation cache and compatible settings/runtime receipts. Preserve and reconcile them; neither reservations nor historical exclusions expire.
- The shared reader requires JavaScript. A local build or Git push alone does not prove deployment; verify the corresponding Pages run and live article.
