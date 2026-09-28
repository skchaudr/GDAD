# Stage 0 watch log — agentos-dashboard

Dated entries, most recent last. Watcher: GLM (Cline) on sab-mini. Facts only; judgment
stays in the roadmap and the invariants doc.

## 2026-09-27 — baseline snapshot

**Graph**: `gddp-config/graphs/agentos-dashboard` — 12 capability nodes charted 2026-08-23.
Arc: contract → schema+watcher ∥ shell+components ∥ API → live-integration → dogfood →
rollout. DAG verified consistent: every `depends_on` has a matching `unlocks`, no cycles.
Frontier arithmetic: only `scope-contract` complete → frontier = {data-topology-schema,
frontend-shell}.

**Evidence vs status — statuses are honest, zero nodes done (Sab, 2026-09-27):**

| Node | Stray output on disk (never judged) | Recorded status |
|---|---|---|
| scope-contract | evidence/01 bundle | complete |
| data-topology-schema | 02 bundle (schema doc, graph.schema.json, validator, sample) — one-shot run output | pending |
| frontend-shell | product repo commit 413152a — fails its own criteria (no build pass, hardcoded placeholders, no test runner) | pending |
| other nine | none | pending |

Watch-log correction 2026-09-27: the first version of this entry read "evidence landed,
statuses lagged" and called the frontier dishonest. That inverted the evidence ladder —
artifacts existing is not work done. Zero nodes have been done; the status files and the
frontier were accurate. MAP.md remains stale on scope-contract (says "planned"; graph
records complete).

`project.yaml.bak` sits in the tree. No `agentos-dashboard` receipts exist anywhere in
`verification/` — zero nodes have been through the evaluator. The stray bundles are
exactly the roadmap §4 hazard observed live: work outside the loop, waiting for no one.


**Product repo** (`~/repos/agentos-dashboard`, no remote): 5 commits. Beyond the shell
commit: "Initial baseline" + "Core project docs added" — an `agent-os/` doc set
(ARCHITECTURE, PRINCIPLES, SKILLS, OBSERVABILITY, …) no node claims yet. Two commits,
one disk.

**Proposals**: 7 milestone restructure (m1–m7, authored 2026-08-29 by opus-5-planner),
frontier-invisible per the mechanism. Notable content: three spec-vs-vault contradictions
already found (vault router is `AGENTS.md` not `CLAUDE.md`; department routers absent;
no `model` frontmatter field) — the `radial-dag` `why` still names hubs the vault lacks.
Five named blockers, the top one human-owned: executor choice (claude -p vs pi vs dsh)
before anything gains the ability to spawn processes.

## 2026-09-27 — frontier node evaluation (dispatch-readiness, per Sab)

Both frontier nodes right in shape; defects below. Evidence: product repo build run live
(exit 0, 283ms), package.json, src/main.jsx, src/styles.css, evidence/01-scope-contract.md,
vault and skills-dir listing.

**frontend-shell** — dispatchable; largely pre-satisfied by the existing scaffold
(build passes, exact theme tokens in `@theme`, Tailwind 4 in use, hash mode switching,
perimeter placeholders naming their owning nodes). Defects: (1) `perimeter` criterion's
"wired to their future data" is uncheckable prose — hardcoded clock/routines strings
pass or fail on the evaluator's reading; specify static placeholder + named slot.
(2) `build` criterion's "no console errors" has no named check method.

**data-topology-schema** — dispatchable after two fixes: (1) `required_artifacts` omits
the validator that the `frontmatter` criterion requires. (2) Its `sample` criterion
references node 01's data-source table, which has rotted: claims `00 Inbox` / `01
Projects` / `02 Areas` "verified live 2026-08-23," actual vault top level is `01_INBOX` /
`02_PROCESS` / `03_COMPLETE` / `04 Periodic`. Root paths real (SSD, ~/.hermes/cron,
both skills dirs). The scope doc is self-marked "DRAFT — adjust any line and re-accept";
that re-acceptance is Sab's and gates this dispatch.

Unevaluated 02 bundle sits in evidence/ — grok's attempt starts from it or fresh;
encode the choice in the dispatch.

## Open — watching for


1. First dispatch → receipt on a real node (has never happened on this graph).
2. First status transition — and whether node YAML, project.yaml, and MAP.md update
   together or diverge further.
3. Whether cursor grok's node creation touches graph files directly or routes through
   proposals/.
