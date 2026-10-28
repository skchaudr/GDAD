import { test, type TestContext } from 'node:test';
import assert from 'node:assert/strict';
import { createActor, SimulatedClock, type ActorRefFrom } from 'xstate';
import { machine, dispatch, commit, receipt, type Receipt, type ScenarioEvent } from './gdad.machine.ts';
function start(testContext: TestContext, scenario: ScenarioEvent | null = 'RUN_PASS') {
  const clock = new SimulatedClock();
  const actor = createActor(machine, { clock }).start();
  testContext.after(() => actor.stop());
  if (scenario) actor.send({ type: scenario });
  return { actor, clock };
}
function complete(actor: ActorRefFrom<typeof machine>, result: Receipt = receipt) {
  actor.send({ type: 'COMMIT_RECEIVED', commit: structuredClone(commit) });
  actor.send({ type: 'RECEIPT_RECEIVED', receipt: structuredClone(result) });
}

test('automatic sample reaches provisional and waits for a human', (testContext) => {
  const { actor, clock } = start(testContext);
  assert.equal(actor.getSnapshot().value, 'AwaitingWork');
  clock.increment(2000);
  assert.equal(actor.getSnapshot().value, 'AwaitingEvaluation');
  assert.equal(actor.getSnapshot().context.commit!.sha, commit.sha);
  assert.equal(actor.getSnapshot().context.receipt, null);
  clock.increment(2000);
  assert.equal(actor.getSnapshot().value, 'Provisional');
  assert.equal(actor.getSnapshot().context.receipt!.criteria.length, 2);
  clock.increment(60000);
  assert.equal(actor.getSnapshot().value, 'Provisional');
  assert.equal(actor.getSnapshot().context.decision, null);
});

test('explicit records reach provisional; human acceptance binds to that work', (testContext) => {
  const { actor } = start(testContext);
  complete(actor);
  assert.equal(actor.getSnapshot().value, 'Provisional');
  actor.send({ type: 'HUMAN_ACCEPTED' });
  assert.equal(actor.getSnapshot().value, 'Accepted');
  const decision = actor.getSnapshot().context.decision;
  assert.ok(decision);
  assert.equal(decision.node, commit['GDAD-Node']);
  assert.equal(decision.attempt, dispatch.attempt);
  assert.equal(decision.sha, commit.sha);
  assert.equal(decision.decision, 'accept');
});

test('human rejection retains the passing receipt', (testContext) => {
  const { actor } = start(testContext);
  complete(actor);
  actor.send({ type: 'HUMAN_REJECTED' });
  assert.equal(actor.getSnapshot().value, 'Rejected');
  assert.equal(actor.getSnapshot().context.receipt!.verdict, 'pass');
  assert.equal(actor.getSnapshot().context.decision!.decision, 'reject');
});

for (const [field, value] of [
  ['node', 'another-node'],
  ['attempt', 2],
  ['sha', 'another-commit'],
  ['pass', 'milestone-1'],
] as const) {
  test(`a different ${field} cannot establish provisional progress`, (testContext) => {
    const { actor } = start(testContext);
    complete(actor, { ...receipt, [field]: value });
    assert.equal(actor.getSnapshot().value, 'UnmatchedReceipt');
    assert.equal(actor.getSnapshot().context.commit!.sha, commit.sha);
    assert.equal(actor.getSnapshot().context.receipt![field], value);
    assert.equal(actor.getSnapshot().context.decision, null);
  });
}

test('a failing receipt preserves work and findings without starting a retry', (testContext) => {
  const { actor, clock } = start(testContext);
  complete(actor, {
    ...receipt,
    verdict: 'fail',
    criteria: [{ id: 'c2', met: false, evidence: 'tests/auth/refresh.race.test.ts:18' }],
    findings: [{ kind: 'broken', what: 'Two refreshes observed', where: 'src/auth/refresh.ts:42' }],
  });
  assert.equal(actor.getSnapshot().value, 'EvaluatedFail');
  clock.increment(60000);
  assert.equal(actor.getSnapshot().value, 'EvaluatedFail');
  assert.equal(actor.getSnapshot().context.dispatch.attempt, 1);
  assert.equal(actor.getSnapshot().context.receipt!.findings.length, 1);
});

test('missing receipt leaves evaluation pending', (testContext) => {
  const { actor } = start(testContext);
  actor.send({ type: 'COMMIT_RECEIVED', commit: structuredClone(commit) });
  assert.equal(actor.getSnapshot().value, 'AwaitingEvaluation');
  assert.equal(actor.getSnapshot().context.receipt, null);
  assert.equal(actor.getSnapshot().context.decision, null);
});

test('a receipt without a final judgment remains unfinished', (testContext) => {
  const { actor } = start(testContext);
  const unfinished = { ...receipt };
  delete unfinished.verdict;
  complete(actor, unfinished);
  assert.equal(actor.getSnapshot().value, 'UnfinishedEvaluation');
  assert.equal(actor.getSnapshot().context.commit!.sha, commit.sha);
});

test('executor record retains trailer names; assigned attempt stays in dispatch', (testContext) => {
  const { actor, clock } = start(testContext);
  clock.increment(2000);
  const context = actor.getSnapshot().context;
  assert.ok(context.commit);
  assert.equal(context.commit['GDAD-Node'], 'auth-refresh');
  assert.equal(context.commit['GDAD-At'], 'done');
  assert.equal(context.dispatch.attempt, 1);
  assert.equal('work' in context, false);
  assert.equal('attempt' in context.commit, false);
});


test('scenario choice is explicit before sample execution begins', (testContext) => {
  const { actor, clock } = start(testContext, null);
  clock.increment(60000);
  assert.equal(actor.getSnapshot().value, 'ChooseScenario');
  assert.equal(actor.getSnapshot().context.commit, null);
});

for (const [scenario, expected] of [
  ['RUN_PASS', 'Provisional'],
  ['RUN_FAIL', 'EvaluatedFail'],
  ['RUN_NO_RECEIPT', 'AwaitingEvaluation'],
  ['RUN_OTHER_COMMIT', 'UnmatchedReceipt'],
] as const) {
  test(`${scenario} automatically reaches ${expected}`, (testContext) => {
    const { actor, clock } = start(testContext, scenario);
    clock.increment(2000);
    assert.equal(actor.getSnapshot().value, 'AwaitingEvaluation');
    clock.increment(2000);
    assert.equal(actor.getSnapshot().value, expected);
    clock.increment(60000);
    assert.equal(actor.getSnapshot().value, expected);
    const context = actor.getSnapshot().context;
    assert.equal(context.commit!.sha, commit.sha);
    assert.equal(context.decision, null);
    if (scenario === 'RUN_FAIL') {
      assert.equal(context.receipt!.criteria[1].met, false);
      assert.equal(context.receipt!.findings.length, 1);
    }
    if (scenario === 'RUN_NO_RECEIPT') assert.equal(context.receipt, null);
    if (scenario === 'RUN_OTHER_COMMIT') assert.notEqual(context.receipt!.sha, context.commit!.sha);
  });
}


test('an explicit unevaluated verdict preserves the commit and receipt', (testContext) => {
  const { actor } = start(testContext);
  complete(actor, { ...receipt, verdict: 'unevaluated', criteria: [], findings: [] });
  assert.equal(actor.getSnapshot().value, 'UnfinishedEvaluation');
  assert.equal(actor.getSnapshot().context.commit!.sha, commit.sha);
  assert.equal(actor.getSnapshot().context.receipt!.verdict, 'unevaluated');
  assert.equal(actor.getSnapshot().context.decision, null);
});

test('known model limit: a pass verdict with empty criteria reaches provisional', (testContext) => {
  const { actor } = start(testContext);
  complete(actor, { ...receipt, criteria: [] });
  assert.equal(actor.getSnapshot().value, 'Provisional');
});

test('known model limit: a pass verdict with an unmet criterion reaches provisional', (testContext) => {
  const { actor } = start(testContext);
  complete(actor, { ...receipt, criteria: [{ ...receipt.criteria[0], met: false }] });
  assert.equal(actor.getSnapshot().value, 'Provisional');
});
