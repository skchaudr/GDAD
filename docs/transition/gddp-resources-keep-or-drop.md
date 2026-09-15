---
title: GDDP — resources worth keeping
date: 2026-09-09
status: draft
tags: [gddp, rebuild, inventory]
---

# GDDP — resources worth keeping

Companion to [[gddp-cli-first-principles-spec]] and [[gddp-rebuild-roadmap]].

Verdicts:

- **ADOPT** — carry forward roughly as-is. The artifact itself is good.
- **INFLUENCE** — the idea survives, the implementation does not. Reimplement from the idea.
- **ARCHIVE** — evidence of a lesson already learned. Read once, don't carry.
- **DROP** — exists to compensate for something the rebuild removes.

Honesty note: I read in full the items marked ✓. Items marked ○ I sized and sampled
but did not read end to end — verdicts on those are provisional and yours to overrule.

---

## ADOPT

### ✓ `docs/invariants/AGENTS.md` — the invariant manifest schema
The single most valuable artifact in either repo. Each entry:

```
id · name · is_invariant · invariant (canonical ref) · rule
current_implementation · drift_pattern · source
```

Three properties make it work, and all three should be non-negotiable in the rebuild:

1. **`rule` is implementation-agnostic; `current_implementation` is explicitly not.**
   That separation is the mechanism you described — it's what keeps an invariant
   distinguishable from the code it governs, so an agent can conclude "this violates
   intent" instead of "this *is* intent."
2. **`is_invariant: false` entries exist.** The single-armed-control-plane entry declares
   current deployment reality as *not* permanent, and names the drift pattern as
   "treating single-host topology as an immutable architectural invariant." That's an
   explicit anti-ossification slot. Most projects have no way to say "this is true today
   and you may change it."
3. **`drift_pattern` states the failure mode, not just the rule.** An agent recognizing a
   shape it's about to produce is worth more than an agent reading a prohibition.

### ✓ Placed subsystem manifests
Seven of them: `deploy/`, `entities/`, `events/`, `jobs/`, `node_status_history/`,
`scripts/`, `docs/invariants/`. Co-located with the code they govern, indexed from one
master. This is the load-reduction mechanism — an agent working in `jobs/` reads one
bounded file, not a scattered doctrine corpus.

### ✓ `AGENTS.md` § "Common failure pattern (2026-07-30)"
The four-step snowball (assume → design on the assumption → fail → invent machinery that
becomes architecture) plus **"None of the architecture or implementation is considered
sacred or unchallengeable."** This is the line that hasn't moved, and it's the direct
counter to the artifact/intent confusion. It goes in the root manifest of the rebuild on
day one, before there is any architecture to protect.

### ✓ `docs/decisions/GDDP-becomes-small-and-real.md` — the scope boundary
GDDP is four things: the graph, the evaluator's canonical-doc + DAG-neighborhood context,
the typed verdict, the human completion gate. And: **"GDDP doesn't rebuild the loop."**
This is the acceptance test for scope. Anything that isn't one of the four, or is the
loop, is out.

### ✓ `docs/decisions/GDDP-rebuild.md` — the diagnosis and the standing rule
*"Agents add. They almost never remove."* · *"Not bad code — unchosen code."* · and the
standing rule: **establish what a layer is compensating for before adding it; prefer
deleting a mechanism to guarding it.** The rule was in a decisions doc, which is why it
didn't fire. In the rebuild it's a manifest entry at every site.

### ✓ `docs/decisions/Tests-can-fail-nodes-can-pass.md` — the evidence ladder
Tests are evidence. Criteria are evidence. Verdicts are evidence. Only human-accepted
status is graph truth. Clean, small, and it forecloses a whole class of agent error.

### ✓ Invariant #4 — Storage & Evidence Doctrine
Durable files and git refs are truth; SQLite is a rebuildable index and can be purged
with nothing of architectural value lost. Genuinely good primitive, and it should
constrain the rebuild: if a fact only exists in a database, it isn't a fact.

### ✓ Invariant #2 — retry immutability + continuation proposals
A retry re-attempts the same node unchanged; findings inject as a fix-list only. Work
discovered out of scope becomes a **frontier-invisible** proposal YAML that only a human
materializes. Small mechanism, prevents the exact scope-creep that produced 78k lines.

### ✓ Handoff template discipline
`Agent Section` above the line, Sab's narrative below, agents forbidden to cross it. The
structural separation of machine report from human interpretation is right, and cheap.

### ✓ `AGENTS.md` § "Strict compliance" — the two-register rule
> *"Do NOT use 'not' or other negative phrasing. If you need to express the negation of a
> concept, use the opposite positive phrase."*

This governs how an agent **talks to Sab**. Answering "what is X" with "X is not Y" spends
attention and delivers nothing; state what X is. It is a conversational rule and it holds.

It does **not** govern how invariants are written, and the two must stay separate:

| Register | Audience | Negation |
|---|---|---|
| Communication | Sab, in conversation | Avoid. State the positive. |
| Guardrail | An agent about to act | Required. `drift_pattern` names the failure shape. |

A manifest entry pairs a positive `rule` with a named `drift_pattern` on purpose — an
agent recognizing the shape it is about to produce is worth more than one reading a
prohibition. Carry both rules into the rebuild, labeled by register so a later session
doesn't read one as contradicting the other.

---

## INFLUENCE

### ✓ Evaluator context policy — the core intellectual asset
The evaluator reads canonical docs (README / brief / foundational node) + the DAG
neighborhood + deterministic evidence, and explicitly **does not read AGENTS.md**,
because that's executor-facing framing. Invariant #3 states it as
"Context Separation Between Execution and Evaluation." This idea is the reason GDDP
deserves to exist. The implementation around it is not.

### ✓ The verdict contract shape
`verdict` · `intent_preserved` · `graph_integrity_preserved` · `criteria_result` ·
`evidence[]` · `required_human_review`. Adopt the shape. The graduation from
criteria-shaped to intent/integrity-shaped is recorded in `GDDP-becomes-small-and-real.md`
and is the right destination — but note it's now downstream of a premise you dropped
(see roadmap §1).

### ✓ `scripts/runtime/verification/schemas.py` (276) — the typed evaluator records
`GraphObservation`, `IntegrityFinding`, `GraphRecommendation` (8 typed graph actions,
non-empty evidence enforced by `Field(min_length=1)`), `CriterionJudgment`, `LaneCoverage`.
Adopt the types; they're the evaluator's vocabulary and already carry the "affects verdict /
doesn't" distinction in their docstrings. Leave behind the `VerdictReceipt` fields that
belong to dropped machinery: `expected_base_commit_sha`, `merge_commit_sha`, `pr_ref`,
`mission_receipt_id`. Reconcile the two verdict vocabularies (`Verdict` enum vs.
`IntegrityOutput.verdict`) into one.

### ✓ Provisional continuation — the separation, not the machinery
The real insight: **execution eligibility and graph truth are two questions, and
`complete` was carrying both.** Keep that. Drop the implementation (reconcile-phase
writer, status-history plumbing, two dependency-gate call sites in different repos) —
most of it disappears if progress lives in its own file (roadmap §4).

### ✓ Two-lane evaluation, worst-of
Deterministic lane + semantic lane, combined worst-of into one receipt. Good shape,
cheap to restate, expensive as built.

### ✓ `docs/gddp-cli-reduction.plan.md` §3–§4 — operator IA + navigation contract
The target information architecture and the navigation contract (every screen is a
picker; Esc is back; `_pause` only after a mutation; no footer whose next step is a shell
command) are good design work independent of the tree they were written against. Carry
the contract into the input layer of the rebuild so no individual screen can opt out.

### ✓ Node YAML schema
`node_id · title · type · why · depends_on · acceptance_criteria[{id,criterion}] ·
constraints · allowed_execution_modes · required_artifacts · priority · unlocks`. Good
shape. `why` in particular is the field that lets an evaluator judge intent at all.
Carry it forward **minus `status`** — see roadmap §4.

---

## ARCHIVE

### ✓ `docs/proposals/simplification-proposal.md` (535)
The best available record of what accretion looks like from the inside, including a
finding it corrects mid-document (§2.2 `node_status_history.py` marked ORPHAN, then
**"WRONG — LIVE"** after a deletion was already authorized on it). Keep as a case study.
Do not use as a work order for a tree you're replacing.

### ✓ `docs/gddp-cli-reduction.plan.md` §1–§2, §7 (as evidence)
§2 is an honest behavioral inventory and §7 is honest about sizing. Also the provenance
lesson: the "2500" you were told appears nowhere in the committed document. Both worth
keeping for what they demonstrate about trusting agent-produced plans.

### ○ The reckoning / postmortem corpus
`docs/learning/reckoning-2026-07-31.md` (325), `building-blocks-reckoning.md` (249),
`blocking-mechanisms-register.md` (156), `postmortem-2026-08-05-vm-harness-audit-canary.md`
(146), `postmortem-canary-scope-2026-07-12.md` (67). Read-once lesson corpus. If any
contains a mechanism worth adopting, it should be promoted to a manifest entry rather
than carried as prose.

### ○ `docs/learning/One Truth, Two Representations.md` (666)
Largest learning doc, unread by me. Title suggests it addresses the config/runtime
representation split, which is upstream of roadmap §4. **Read this before deciding
§4** — it may already contain your answer.

---

## DROP

### ✓ Everything downstream of patch-return
`expected_base_commit_sha` binding, base-SHA mismatch rejection, patch spool, changeSet
hunting, `_REMOTE_BRANCHING_EXECUTORS` preflight. `GDDP-rebuild.md` already traces all
five layers to one unset config field. Nothing to port.

### ✓ The frozen-infrastructure list
`intake_server.py`, `jules_*` adapters, `rig1-heartbeat/`, `deploy.sh`, `rollback.py`,
`export_evaluations.py` marked frozen, zero speculative investment. Freezing is what you
do to code you can't justify and can't remove. In a rebuild the list should be empty —
if something can't be justified, it doesn't get written.

### ○ `docs/proposals/executor-capability-contract.md` (1002)
Unread, but 1002 lines specifying executor capability is the exact shape of the disease:
GDDP does not own the executors, and a contract this large is completeness-optimization
for a boundary that should be "executors are replaceable transports." Sanity-check me
before dropping.

### ✓ ByteRover section
Self-expiring 2026-09-30. Nothing to carry.
