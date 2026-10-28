import { createActor, SimulatedClock } from 'xstate';
import { machine, receipt, type ScenarioEvent } from './gdad.machine.ts';

const scenarios: Record<string, {
  event: ScenarioEvent;
  decision?: 'HUMAN_ACCEPTED' | 'HUMAN_REJECTED';
  unfinished?: boolean;
}> = {
  pass: { event: 'RUN_PASS' },
  accept: { event: 'RUN_PASS', decision: 'HUMAN_ACCEPTED' },
  reject: { event: 'RUN_PASS', decision: 'HUMAN_REJECTED' },
  fail: { event: 'RUN_FAIL' },
  pending: { event: 'RUN_NO_RECEIPT' },
  mismatch: { event: 'RUN_OTHER_COMMIT' },
  unevaluated: { event: 'RUN_NO_RECEIPT', unfinished: true },
};

const requested = process.argv.slice(2);
const selected = requested.length ? requested : Object.keys(scenarios);
const unknown = selected.filter(name => !Object.hasOwn(scenarios, name));
if (unknown.length) {
  process.stderr.write(`Unknown scenarios: ${unknown.join(', ')}\nChoose: ${Object.keys(scenarios).join(', ')}\n`);
  process.exit(1);
}

for (const name of selected) {
  const scenario = scenarios[name];
  const clock = new SimulatedClock();
  const actor = createActor(machine, { clock });
  const states: string[] = [];
  actor.subscribe(snapshot => {
    const state = String(snapshot.value);
    if (states.at(-1) !== state) states.push(state);
  });
  try {
    actor.start();
    actor.send({ type: scenario.event });
    clock.increment(2000);
    clock.increment(2000);
    if (scenario.unfinished) {
      actor.send({
        type: 'RECEIPT_RECEIVED',
        receipt: { ...structuredClone(receipt), verdict: 'unevaluated', criteria: [], findings: [] },
      });
    }
    if (scenario.decision) actor.send({ type: scenario.decision });
    const { dispatch, commit, receipt: result, decision } = actor.getSnapshot().context;
    process.stdout.write(JSON.stringify({ scenario: name, states, dispatch, commit, receipt: result, decision }, null, 2) + '\n');
  } finally {
    actor.stop();
  }
}
