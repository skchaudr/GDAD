# Stage 0 — evidence-gathering brief

For the setup agents running the existing (old) GDDP on sab-mini. Written so the work
stays inside roadmap §9 stage 0: **evidence only, abandonable, no investment.**

## Goal

Run the existing GDDP end-to-end with cheap executors against real nodes, purely to gather
evidence for the rebuild. Success = the rebuild learns lessons it would otherwise learn the
hard way.

## Deliverables

1. **Receipts** — at least one full dispatch → evaluation → receipt cycle on a real node,
   using the cheapest executor available (grok 4.6/4.7 via the existing cursor executor
   path; `deepseek-v4-flash` is the reference cheap executor in `scripts/gddp.py`).
2. **One live example of every transition** — dispatch, receipt write, provisional advance,
   reject/retry, and (operator-performed) accept. Where a transition can't be triggered
   honestly, record that with the reason — a gap is also evidence.
3. **A short log** — what worked, what broke, what the rebuild should encode that the old
   system had to bolt on. Read once, then it's done.

## Constraints

- The old repos (`gddp-config`, `gddp-runtime`) are **reference, read-only**: runtime state
  (spool, receipts, worktrees) only; no code changes, no schema changes, no "quick fixes."
- Stage 0 blocks nothing and receives no investment. If setup exceeds ~2 hours of agent
  effort, stop and report instead of engineering around it.
- Evidence is disposable: worst case it's abandonable, which has already happened and
  costs nothing.

## Known state on sab-mini (2026-09-27)

- Entry point: `/Users/sab-mini/repos/gddp-config/scripts/gddp.py` (6672 lines).
- 27 graphs under `gddp-config/graphs/` — candidates with real history:
  `gddp-dogfood`, `aa-cli-verify`, `aa-cli-tui-pass`, `vault-doctor`.
- launchd: `com.gddp.sync-evidence` loaded and running; `com.gddp.sweep-daily.plist`
  installed but not loaded.
- Receipts land in `~/.gddp/receipts/` (existing: `aa-cli/common-core.json`,
  `vault-doctor/scan-vault-core.json`).
- Operator: run acceptance/merge steps under Sab's identity only; evaluators never accept.

## Out of scope

Improving the old system, porting anything to GDAD, evaluating the new verdict contract
against these receipts (that's the rebuild's job, once receipts exist).
