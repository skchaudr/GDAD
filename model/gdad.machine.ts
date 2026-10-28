// Another unapproved porting that served no need beyond Codex deciding it was writing the project now
import { setup, assign } from 'xstate';

export type Dispatch = { node: string; attempt: number };
export type Commit = { sha: string; 'GDAD-Node': string; 'GDAD-At': string };
export type Receipt = {
  node: string;
  attempt: number;
  sha: string;
  pass: string;
  verdict?: 'pass' | 'fail' | 'unevaluated';
  criteria: { id: string; met: boolean; evidence: string }[];
  findings: { kind: string; what: string; where: string; evidence?: string }[];
  graph: { corrective_nodes: unknown[]; recommendations: unknown[] };
};
export type Decision = Dispatch & { sha: string; decision: 'accept' | 'reject' };
export type ScenarioEvent = 'RUN_PASS' | 'RUN_FAIL' | 'RUN_NO_RECEIPT' | 'RUN_OTHER_COMMIT';
type Context = {
  scenario: 'pass' | 'fail' | 'no-receipt' | 'other-commit' | null;
  dispatch: Dispatch;
  commit: Commit | null;
  receipt: Receipt | null;
  decision: Decision | null;
  message: string;
};
type Event =
  | { type: ScenarioEvent }
  | { type: 'COMMIT_RECEIVED'; commit: Commit }
  | { type: 'RECEIPT_RECEIVED'; receipt: Receipt }
  | { type: 'HUMAN_ACCEPTED' | 'HUMAN_REJECTED' };

export const dispatch: Dispatch = { node: 'auth-refresh', attempt: 1 };
export const commit: Commit = {
  sha: 'd4e5f6',
  'GDAD-Node': 'auth-refresh',
  'GDAD-At': 'done',
};
export const receipt: Receipt = {
  node: dispatch.node,
  attempt: dispatch.attempt,
  sha: commit.sha,
  pass: 'final',
  verdict: 'pass',
  criteria: [
    { id: 'c1', met: true, evidence: 'tests/auth/refresh.test.ts:12' },
    { id: 'c2', met: true, evidence: 'tests/auth/refresh.race.test.ts:18' },
  ],
  findings: [],
  graph: { corrective_nodes: [], recommendations: [] },
};

export const machine = setup({
  types: {
    context: {} as Context,
    events: {} as Event,
  },
  guards: {
    suppliesReceipt: ({ context }) => context.scenario !== 'no-receipt',
    matchesCommit: ({ context }) => {
      const result = context.receipt;
      const work = context.commit;
      const assigned = context.dispatch;
      return Boolean(result && work && result.node === work['GDAD-Node'] &&
        result.node === assigned.node && result.attempt === assigned.attempt &&
        result.sha === work.sha && work['GDAD-At'] === 'done' && result.pass === 'final');
    },
    passed: ({ context }) => context.receipt?.verdict === 'pass',
    failed: ({ context }) => context.receipt?.verdict === 'fail',
  },
  actions: {
    saveCommit: assign({
      commit: ({ context, event }) => event.type === 'COMMIT_RECEIVED' ? event.commit : context.commit,
      message: 'Completed work recorded; evaluation is pending.',
    }),
    sampleCommit: assign({
      commit: () => ({ ...commit }),
      message: 'Sample executor supplied completed work; evaluation is pending.',
    }),
    saveReceipt: assign({
      receipt: ({ context, event }) => event.type === 'RECEIPT_RECEIVED' ? event.receipt : context.receipt,
    }),
    sampleReceipt: assign({
      receipt: ({ context }) => {
        const result = structuredClone(receipt);
        if (context.scenario === 'fail') {
          result.verdict = 'fail';
          result.criteria[1].met = false;
          result.findings = [{
            kind: 'broken', what: 'Concurrent requests caused two refreshes',
            where: 'src/auth/refresh.ts:42',
            evidence: 'tests/auth/refresh.race.test.ts:18',
          }];
        }
        if (context.scenario === 'other-commit') result.sha = 'another-commit';
        return result;
      },
    }),
    accept: assign({
      decision: ({ context }): Decision => ({
        node: context.commit!['GDAD-Node'], attempt: context.dispatch.attempt,
        sha: context.commit!.sha, decision: 'accept',
      }),
    }),
    reject: assign({
      decision: ({ context }): Decision => ({
        node: context.commit!['GDAD-Node'], attempt: context.dispatch.attempt,
        sha: context.commit!.sha, decision: 'reject',
      }),
    }),
  },
}).createMachine({
  id: 'GDAD',
  initial: 'ChooseScenario',
  context: () => ({
    scenario: null,
    dispatch: { ...dispatch },
    commit: null,
    receipt: null,
    decision: null,
    message: 'Choose a scenario. Sample handoffs then run automatically; acceptance remains your decision.',
  }),
  states: {
    ChooseScenario: {
      on: {
        RUN_PASS: { target: 'AwaitingWork', actions: assign({ scenario: 'pass' }) },
        RUN_FAIL: { target: 'AwaitingWork', actions: assign({ scenario: 'fail' }) },
        RUN_NO_RECEIPT: { target: 'AwaitingWork', actions: assign({ scenario: 'no-receipt' }) },
        RUN_OTHER_COMMIT: { target: 'AwaitingWork', actions: assign({ scenario: 'other-commit' }) },
      },
    },
    AwaitingWork: {
      after: { 2000: { target: 'AwaitingEvaluation', actions: 'sampleCommit' } },
      on: {
        COMMIT_RECEIVED: { target: 'AwaitingEvaluation', actions: 'saveCommit' },
      },
    },
    AwaitingEvaluation: {
      after: { 2000: { guard: 'suppliesReceipt', target: 'CheckBinding', actions: 'sampleReceipt' } },
      on: {
        RECEIPT_RECEIVED: { target: 'CheckBinding', actions: 'saveReceipt' },
      },
    },
    CheckBinding: {
      always: [
        { guard: 'matchesCommit', target: 'ReadVerdict' },
        { target: 'UnmatchedReceipt' },
      ],
    },
    ReadVerdict: {
      always: [
        { guard: 'passed', target: 'Provisional' },
        { guard: 'failed', target: 'EvaluatedFail' },
        { target: 'UnfinishedEvaluation' },
      ],
    },
    Provisional: {
      entry: assign({ message: 'Matching passing receipt recorded. Human acceptance remains a separate decision.' }),
      on: {
        HUMAN_ACCEPTED: { target: 'Accepted', actions: 'accept' },
        HUMAN_REJECTED: { target: 'Rejected', actions: 'reject' },
      },
    },
    EvaluatedFail: {
      entry: assign({ message: 'Matching failure receipt recorded. Work and findings remain available; this model schedules no retry.' }),
    },
    UnmatchedReceipt: {
      entry: assign({ message: 'Receipt does not identify this node, attempt, final checkpoint, and commit. Evaluation of this work remains unfinished.' }),
    },
    UnfinishedEvaluation: {
      entry: assign({ message: 'Receipt supplies no final pass/fail judgment. Work remains available and evaluation remains unfinished.' }),
    },
    Accepted: { type: 'final' },
    Rejected: { type: 'final' },
  },
});
