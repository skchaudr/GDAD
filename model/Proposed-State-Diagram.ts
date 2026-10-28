
import { setup, assign } from 'xstate';

export const reviewStatus = 'UNAPPROVED REVIEW DRAFT. All example records are synthetic.';
export const reviewNotes = [
  'Starting surface: model/gdad.machine.ts and current/contract-scenarios.md. Added fields and transitions are proposals.',
  'Evidence URIs and timestamps are fixtures. This machine runs in memory; real executors, evaluators and persistence remain external.',
  'The existing verdict-only pass rule is retained, including its documented criterion-completeness and consistency limitation.',
  'These are TypeScript contracts. Runtime validation of arbitrary JSON payloads is a separate, unimplemented boundary.',
];

export type Evidence = { uri: string; description: string };
export type Criterion = { id: string; requirement: string };
export type NodeDefinition = {
  id: string;
  revision: string; // no clue what revision is 
  title: string;
  intent: string; // what is intent lol 
  dependsOn: string[];
  constraints: string[]; // constraints is out bruh 
  criteria: Criterion[]; // not even acceptance criteria 
  sources: Evidence[]; // wtf is sources lol 
};
export type ProjectDefinition = {
  id: string;
  revision: string;
  intent: string;
  invariants: string[];
  sources: Evidence[];
  nodes: NodeDefinition[];
};
export type Binding = {
  project: string;
  projectRevision: string;
  node: string;
  nodeRevision: string;
  attempt: number;
};
export type Finding = {
  kind: 'work' | 'intent' | 'graph' | 'missing-evidence';
  description: string;
  affectedNodes: string[];
  evidence: Evidence[];
};
export type GraphProposal = {
  description: string;
  affectedNodes: string[];
  rationale: string;
  evidence: Evidence[];
};
export type ExecutorInput = {
  id: string;
  binding: Binding;
  canonical: ProjectDefinition;
  dependencies: DependencyRecord[];
  baseSha: string;
  previousFindings: Finding[];
};
export type ExecutorActivity = {
  requestId: string;
  executor: string;
  at: string;
  activity: 'accepted' | 'reading' | 'writing' | 'testing' | 'waiting';
  description: string;
  evidence: Evidence[];
};
export type ExecutorOutput = {
  id: string;
  requestId: string;
  binding: Binding;
  executor: string;
  at: string;
  outcome: 'completed' | 'partial' | 'failed' | 'cancelled';
  summary: string;
  work: { baseSha: string; sha: string; artifacts: Evidence[] } | null;
  evidence: Evidence[];
  errors: string[];
  proposals: GraphProposal[];
};
export type EvaluatorInput = {
  id: string;
  binding: Binding;
  canonical: ProjectDefinition;
  dependencies: DependencyRecord[];
  executorResultId: string;
  work: ExecutorOutput['work'];
  executionEvidence: Evidence[];
  executionErrors: string[];
  checkpoint: 'final';
};
export type CriterionJudgment = {
  id: string;
  judgment: 'met' | 'unmet' | 'undetermined';
  reasoning: string;
  evidence: Evidence[];
};
export type EvaluationReport = {
  criteria: CriterionJudgment[];
  intent: 'preserved' | 'drift' | 'undetermined';
  graph: 'preserved' | 'issue' | 'undetermined';
  reasoning: string;
  findings: Finding[];
  proposals: GraphProposal[];
  inspected: Evidence[];
};
export type EvaluatorOutput = {
  id: string;
  requestId: string;
  binding: Binding;
  evaluator: string;
  at: string;
  executorResultId: string;
  sha: string | null;
  checkpoint: 'final';
  receipt: Evidence;
} & (
  | { outcome: 'completed'; verdict: 'pass' | 'fail' | 'needs-review'; report: EvaluationReport }
  | { outcome: 'unfinished'; reason: string; partialReport: EvaluationReport | null }
);
export type HumanDecision = {
  id: string;
  binding: Binding;
  executorResultId: string;
  sha: string | null;
  human: string;
  at: string;
  decision: 'accept' | 'reject';
  reason: string;
};
export type DependencyRecord = {
  node: string;
  binding: Binding | null;
  work: ExecutorOutput['work'];
  evaluation: EvaluatorOutput | null;
  decision: HumanDecision | null;
};
export type Attempt = {
  input: ExecutorInput;
  activity: ExecutorActivity[];
  output: ExecutorOutput | null;
  evaluationInputs: EvaluatorInput[];
  evaluations: EvaluatorOutput[];
  evaluationPending: boolean;
  decisions: HumanDecision[];
};
export type NodeView = {
  node: string;
  title: string;
  attempt: number | null;
  execution: 'unstarted' | 'requested' | 'active' | ExecutorOutput['outcome'];
  evaluation: 'unrequested' | 'pending' | 'unmatched' | 'unfinished' | 'completed';
  verdict: 'pass' | 'fail' | 'needs-review' | null;
  humanDecision: 'accept' | 'reject' | null;
  provisional: boolean;
  eligible: boolean;
  waitingOn: string[];
  lastActivity: ExecutorActivity | null;
  work: ExecutorOutput['work'];
  findings: Finding[];
  proposals: GraphProposal[];
  evidence: Evidence[];
};
export type Context = {
  project: ProjectDefinition;
  selectedNode: string;
  scenario: 'pass' | 'fail' | 'pending' | 'mismatch' | 'unfinished' | 'executor-fail';
  attempts: Attempt[];
  rejectedInputs: { event: unknown; reason: string }[];
  view: NodeView[];
};
export type Event =
  | { type: 'RUN_PASS' | 'RUN_FAIL' | 'RUN_NO_RECEIPT' | 'RUN_OTHER_COMMIT' | 'RUN_UNFINISHED' | 'RUN_EXECUTOR_FAIL' }
  | { type: 'EXECUTOR_ACTIVITY'; activity: ExecutorActivity }
  | { type: 'EXECUTOR_RETURNED'; result: ExecutorOutput }
  | { type: 'EVALUATOR_RETURNED'; result: EvaluatorOutput }
  | { type: 'HUMAN_DECIDED'; decision: HumanDecision }
  | { type: 'SELECT_NODE'; node: string }
  | { type: 'RETURN_SAMPLE_WORK' | 'RETURN_SAMPLE_EVALUATION' | 'HUMAN_ACCEPTED' | 'HUMAN_REJECTED' | 'RETRY_WORK' | 'RECOVER_EVALUATION' | 'NEXT_EXAMPLE_NODE' };

export const exampleProject: ProjectDefinition = {
  id: 'example-refresh', revision: 'draft-1',
  intent: 'Refresh expired sessions without duplicating concurrent refreshes.',
  invariants: ['Human acceptance remains separate from evaluation.', 'Preserve work and evaluation evidence.'],
  sources: [{ uri: 'example://project/intent', description: 'Synthetic project intent' }],
  nodes: [
    {
      id: 'auth-refresh', revision: 'draft-1', title: 'Refresh a session once',
      intent: 'Concurrent requests share one refresh operation.', dependsOn: [],
      constraints: ['Keep existing authentication behavior.'],
      criteria: [
        { id: 'c1', requirement: 'An expired session can be refreshed.' },
        { id: 'c2', requirement: 'Concurrent requests cause one refresh.' },
      ],
      sources: [{ uri: 'example://nodes/auth-refresh', description: 'Synthetic node definition' }],
    },
    {
      id: 'refresh-client', revision: 'draft-1', title: 'Use refresh in the client',
      intent: 'Client requests resume after a shared refresh.', dependsOn: ['auth-refresh'],
      constraints: ['Use the shared refresh behavior.'],
      criteria: [{ id: 'c3', requirement: 'The client retries its request after refresh.' }],
      sources: [{ uri: 'example://nodes/refresh-client', description: 'Synthetic dependent node' }],
    },
  ],
};

const timestamp = '2026-10-24T12:00:00Z';
const last = <Item,>(items: Item[]): Item | undefined => items[items.length - 1];
const current = (context: Context): Attempt => last(context.attempts)!;
const nodeFor = (project: ProjectDefinition, id: string): NodeDefinition => project.nodes.find(node => node.id === id)!;
const sameBinding = (first: Binding, second: Binding): boolean =>
  first.project === second.project && first.projectRevision === second.projectRevision &&
  first.node === second.node && first.nodeRevision === second.nodeRevision && first.attempt === second.attempt;

function matchesEvaluation(attempt: Attempt, receipt: EvaluatorOutput): boolean {
  const request = last(attempt.evaluationInputs);
  return Boolean(request && sameBinding(request.binding, receipt.binding) &&
    request.id === receipt.requestId && request.executorResultId === receipt.executorResultId &&
    (request.work?.sha ?? null) === receipt.sha && request.checkpoint === receipt.checkpoint);
}

function reportFor(receipt: EvaluatorOutput | undefined): EvaluationReport | null {
  return receipt ? receipt.outcome === 'completed' ? receipt.report : receipt.partialReport : null;
}

export function projectView(context: Context): NodeView[] {
  const views = context.project.nodes.map((node): NodeView => {
    const attempt = last(context.attempts.filter(item => item.input.binding.node === node.id));
    const receipt = attempt && !attempt.evaluationPending ? last(attempt.evaluations) : undefined;
    const matched = Boolean(attempt && receipt && matchesEvaluation(attempt, receipt));
    const report = reportFor(receipt);
    const decision = attempt && last(attempt.decisions);
    const output = attempt?.output;
    const completed = matched && receipt?.outcome === 'completed';
    return {
      node: node.id, title: node.title, attempt: attempt?.input.binding.attempt ?? null,
      execution: output?.outcome ?? (attempt ? attempt.activity.length ? 'active' : 'requested' : 'unstarted'),
      evaluation: !attempt?.evaluationInputs.length ? 'unrequested' : !receipt ? 'pending' :
        !matched ? 'unmatched' : receipt.outcome === 'unfinished' ? 'unfinished' : 'completed',
      verdict: completed ? receipt.verdict : null,
      humanDecision: decision?.decision ?? null,
      provisional: completed && receipt.verdict === 'pass' && !decision,
      eligible: false, waitingOn: [], lastActivity: attempt ? last(attempt.activity) ?? null : null,
      work: output?.work ?? null,
      findings: report?.findings ?? [], proposals: [...(output?.proposals ?? []), ...(report?.proposals ?? [])],
      evidence: [...(output?.evidence ?? []), ...(output?.work?.artifacts ?? []), ...(receipt ? [receipt.receipt] : [])],
    };
  });
  return views.map(view => {
    const node = nodeFor(context.project, view.node);
    const waitingOn = node.dependsOn.filter(dependency => {
      const predecessor = views.find(item => item.node === dependency);
      return !predecessor || !(predecessor.humanDecision === 'accept' || predecessor.provisional);
    });
    return { ...view, waitingOn, eligible: view.execution === 'unstarted' && waitingOn.length === 0 };
  });
}

function updateAttempt(context: Context, change: Partial<Attempt>): Attempt[] {
  return [...context.attempts.slice(0, -1), { ...current(context), ...change }];
}

function dependencyRecords(context: Context, node: NodeDefinition): DependencyRecord[] {
  return node.dependsOn.map(dependency => {
    const attempt = last(context.attempts.filter(item => item.input.binding.node === dependency));
    const receipt = attempt && !attempt.evaluationPending ? last(attempt.evaluations) : undefined;
    return structuredClone({
      node: dependency, binding: attempt?.input.binding ?? null, work: attempt?.output?.work ?? null,
      evaluation: attempt && receipt && matchesEvaluation(attempt, receipt) ? receipt : null,
      decision: attempt ? last(attempt.decisions) ?? null : null,
    });
  });
}

export function sampleWork(context: Context): ExecutorOutput {
  const input = current(context).input;
  const failed = context.scenario === 'executor-fail';
  return {
    id: `${input.id}/result`, requestId: input.id, binding: { ...input.binding },
    executor: 'synthetic-executor', at: timestamp,
    outcome: failed ? 'failed' : 'completed',
    summary: failed ? 'Execution stopped; partial work preserved.' : 'Implemented the requested behavior.',
    work: { baseSha: input.baseSha, sha: `example-${input.binding.node}-${input.binding.attempt}`,
      artifacts: [{ uri: `example://${input.id}/diff`, description: 'Synthetic work diff' }] },
    evidence: [{ uri: `example://${input.id}/tests`, description: failed ? 'Synthetic failing test output' : 'Synthetic test output' }],
    errors: failed ? ['Synthetic executor interruption'] : [], proposals: [],
  };
}

export function sampleEvaluation(context: Context): EvaluatorOutput {
  const input = last(current(context).evaluationInputs)!;
  const node = nodeFor(input.canonical, input.binding.node);
  const failed = context.scenario === 'fail' || context.scenario === 'executor-fail';
  const evidence = { uri: `example://${input.id}/inspection`, description: 'Synthetic independent inspection' };
  const report: EvaluationReport = {
    criteria: node.criteria.map((criterion, index) => ({
      id: criterion.id, judgment: failed && index === 0 ? 'unmet' : 'met',
      reasoning: failed && index === 0 ? 'Observed behavior misses this requirement.' : 'Observed behavior satisfies this requirement.',
      evidence: [evidence],
    })),
    intent: failed ? 'undetermined' : 'preserved', graph: 'preserved',
    reasoning: failed ? 'The returned work needs correction.' : 'The returned work satisfies the node in its project context.',
    findings: failed ? [{ kind: 'work', description: 'The required behavior is incomplete.', affectedNodes: [node.id], evidence: [evidence] }] : [],
    proposals: [], inspected: [...input.canonical.sources, ...node.sources, evidence],
  };
  const identity = {
    id: `${input.id}/receipt/${current(context).evaluations.length + 1}`, requestId: input.id,
    binding: { ...input.binding }, evaluator: 'synthetic-independent-evaluator', at: timestamp,
    executorResultId: input.executorResultId,
    sha: context.scenario === 'mismatch' ? 'example-other-commit' : input.work?.sha ?? null,
    checkpoint: 'final' as const,
    receipt: { uri: `example://${input.id}/receipt`, description: 'Synthetic persisted evaluator receipt' },
  };
  return context.scenario === 'unfinished'
    ? { ...identity, outcome: 'unfinished', reason: 'Synthetic evaluator timeout', partialReport: null }
    : { ...identity, outcome: 'completed', verdict: failed ? 'fail' : 'pass', report };
}

function sampleDecision(context: Context, decision: 'accept' | 'reject'): HumanDecision {
  const attempt = current(context);
  return {
    id: `${attempt.input.id}/decision/${attempt.decisions.length + 1}`,
    binding: { ...attempt.input.binding }, executorResultId: attempt.output!.id,
    sha: attempt.output!.work?.sha ?? null, human: 'synthetic-human', at: timestamp,
    decision, reason: `Synthetic ${decision} event; no real work is accepted by this simulation.`,
  };
}

export const machine = setup({
  types: { context: {} as Context, events: {} as Event },
  guards: {
    resultMatches: ({ context, event }) => event.type === 'EXECUTOR_RETURNED' &&
      event.result.requestId === current(context).input.id && sameBinding(event.result.binding, current(context).input.binding),
    activityMatches: ({ context, event }) => event.type === 'EXECUTOR_ACTIVITY' &&
      event.activity.requestId === current(context).input.id,
    evaluationMatches: ({ context }) => matchesEvaluation(current(context), last(current(context).evaluations)!),
    passed: ({ context }) => {
      const receipt = last(current(context).evaluations)!;
      return receipt.outcome === 'completed' && receipt.verdict === 'pass';
    },
    failed: ({ context }) => {
      const receipt = last(current(context).evaluations)!;
      return receipt.outcome === 'completed' && receipt.verdict === 'fail';
    },
    unfinished: ({ context }) => last(current(context).evaluations)!.outcome === 'unfinished',
    canDecide: ({ context }) => Boolean(last(context.attempts)?.output),
    decisionMatches: ({ context, event }) => {
      const attempt = last(context.attempts);
      return Boolean(attempt?.output && event.type === 'HUMAN_DECIDED' &&
        sameBinding(event.decision.binding, attempt.input.binding) && event.decision.executorResultId === attempt.output.id &&
        event.decision.sha === (attempt.output.work?.sha ?? null));
    },
    accepted: ({ context }) => last(current(context).decisions)?.decision === 'accept',
    hasEvaluationInput: ({ context }) => Boolean(last(context.attempts)?.evaluationInputs.length),
    canRetry: ({ context }) => Boolean(last(context.attempts)?.output),
    canSelect: ({ context, event }) => event.type === 'SELECT_NODE' && context.view.some(node => node.node === event.node && node.eligible),
    hasNext: ({ context }) => context.view.some(node => node.eligible),
    sampleReceiptAvailable: ({ context }) => context.scenario !== 'pending' && Boolean(last(context.attempts)?.evaluationInputs.length),
  },
  actions: {
    selectScenario: assign(({ event }) => ({ scenario: ({
      RUN_PASS: 'pass', RUN_FAIL: 'fail', RUN_NO_RECEIPT: 'pending', RUN_OTHER_COMMIT: 'mismatch',
      RUN_UNFINISHED: 'unfinished', RUN_EXECUTOR_FAIL: 'executor-fail',
    } as Record<string, Context['scenario']>)[event.type] ?? 'pass' })),
    prepareWork: assign(({ context }) => {
      const node = nodeFor(context.project, context.selectedNode);
      const previous = last(context.attempts.filter(attempt => attempt.input.binding.node === node.id));
      const attempt = (previous?.input.binding.attempt ?? 0) + 1;
      const input: ExecutorInput = {
        id: `${context.project.id}/${node.id}/${attempt}`,
        binding: { project: context.project.id, projectRevision: context.project.revision, node: node.id, nodeRevision: node.revision, attempt },
        canonical: structuredClone(context.project), dependencies: dependencyRecords(context, node), baseSha: 'example-base',
        previousFindings: (reportFor(previous && last(previous.evaluations))?.findings ?? []).filter(finding => finding.evidence.length),
      };
      return { attempts: [...context.attempts, { input, activity: [], output: null, evaluationInputs: [], evaluations: [], evaluationPending: false, decisions: [] }] };
    }),
    saveActivity: assign(({ context, event }) => event.type === 'EXECUTOR_ACTIVITY'
      ? { attempts: updateAttempt(context, { activity: [...current(context).activity, structuredClone(event.activity)] }) } : {}),
    saveWork: assign(({ context, event }) => event.type === 'EXECUTOR_RETURNED'
      ? { attempts: updateAttempt(context, { output: structuredClone(event.result) }) } : {}),
    sampleWork: assign(({ context }) => ({ attempts: updateAttempt(context, { output: sampleWork(context) }) })),
    prepareEvaluation: assign(({ context }) => {
      const attempt = current(context);
      const output = attempt.output!;
      const input: EvaluatorInput = {
        id: `${attempt.input.id}/evaluation/${attempt.evaluationInputs.length + 1}`,
        binding: { ...attempt.input.binding }, canonical: structuredClone(context.project),
        dependencies: dependencyRecords(context, nodeFor(context.project, attempt.input.binding.node)),
        executorResultId: output.id, work: structuredClone(output.work),
        executionEvidence: structuredClone(output.evidence), executionErrors: [...output.errors], checkpoint: 'final',
      };
      return { attempts: updateAttempt(context, { evaluationInputs: [...attempt.evaluationInputs, input], evaluationPending: true }) };
    }),
    saveEvaluation: assign(({ context, event }) => event.type === 'EVALUATOR_RETURNED'
      ? { attempts: updateAttempt(context, { evaluations: [...current(context).evaluations, structuredClone(event.result)], evaluationPending: false }) } : {}),
    sampleEvaluation: assign(({ context }) => ({ attempts: updateAttempt(context, { evaluations: [...current(context).evaluations, sampleEvaluation(context)], evaluationPending: false }) })),
    saveDecision: assign(({ context, event }) => event.type === 'HUMAN_DECIDED'
      ? { attempts: updateAttempt(context, { decisions: [...current(context).decisions, structuredClone(event.decision)] }) } : {}),
    accept: assign(({ context }) => ({ attempts: updateAttempt(context, { decisions: [...current(context).decisions, sampleDecision(context, 'accept')] }) })),
    reject: assign(({ context }) => ({ attempts: updateAttempt(context, { decisions: [...current(context).decisions, sampleDecision(context, 'reject')] }) })),
    selectNode: assign(({ event }) => event.type === 'SELECT_NODE' ? { selectedNode: event.node, scenario: 'pass' as const } : {}),
    selectNext: assign(({ context }) => ({ selectedNode: context.view.find(node => node.eligible)!.node, scenario: 'pass' as const })),
    rejectInput: assign(({ context, event }) => ({ rejectedInputs: [...context.rejectedInputs, { event: structuredClone(event), reason: 'Input is unavailable or does not match the active handoff.' }] })),
    refreshView: assign(({ context }) => ({ view: projectView(context) })),
  },
}).createMachine({
  id: 'GDADContractReview',
  description: reviewStatus,
  initial: 'ChooseScenario',
  context: () => ({ project: structuredClone(exampleProject), selectedNode: 'auth-refresh', scenario: 'pass', attempts: [], rejectedInputs: [], view: [] }),
  entry: 'refreshView',
  on: {
    EVALUATOR_RETURNED: [
      { guard: 'hasEvaluationInput', target: '.CheckBinding', actions: ['saveEvaluation', 'refreshView'] },
      { actions: 'rejectInput' },
    ],
    RETURN_SAMPLE_EVALUATION: { guard: 'sampleReceiptAvailable', target: '.CheckBinding', actions: ['sampleEvaluation', 'refreshView'] },
    HUMAN_DECIDED: [
      { guard: 'decisionMatches', target: '.ReadDecision', actions: ['saveDecision', 'refreshView'] },
      { actions: 'rejectInput' },
    ],
    HUMAN_ACCEPTED: { guard: 'canDecide', target: '.Accepted', actions: ['accept', 'refreshView'] },
    HUMAN_REJECTED: { guard: 'canDecide', target: '.Rejected', actions: ['reject', 'refreshView'] },
    RETRY_WORK: { guard: 'canRetry', target: '.AwaitingWork', actions: ['prepareWork', 'refreshView'] },
    RECOVER_EVALUATION: { guard: 'hasEvaluationInput', target: '.AwaitingEvaluation', actions: ['prepareEvaluation', 'refreshView'] },
    SELECT_NODE: [
      { guard: 'canSelect', target: '.AwaitingWork', actions: ['selectNode', 'prepareWork', 'refreshView'] },
      { actions: 'rejectInput' },
    ],
    NEXT_EXAMPLE_NODE: { guard: 'hasNext', target: '.AwaitingWork', actions: ['selectNext', 'prepareWork', 'refreshView'] },
  },
  states: {
    ChooseScenario: {
      description: 'Choose synthetic inputs; every request and return remains inspectable in context.attempts.',
      on: {
        RUN_PASS: { target: 'AwaitingWork', actions: ['selectScenario', 'prepareWork', 'refreshView'] },
        RUN_FAIL: { target: 'AwaitingWork', actions: ['selectScenario', 'prepareWork', 'refreshView'] },
        RUN_NO_RECEIPT: { target: 'AwaitingWork', actions: ['selectScenario', 'prepareWork', 'refreshView'] },
        RUN_OTHER_COMMIT: { target: 'AwaitingWork', actions: ['selectScenario', 'prepareWork', 'refreshView'] },
        RUN_UNFINISHED: { target: 'AwaitingWork', actions: ['selectScenario', 'prepareWork', 'refreshView'] },
        RUN_EXECUTOR_FAIL: { target: 'AwaitingWork', actions: ['selectScenario', 'prepareWork', 'refreshView'] },
      },
    },
    AwaitingWork: {
      description: 'Inspect ExecutorInput: canonical project and nodes, selected intent, criteria, constraints, dependencies, sources, base work and cited prior findings.',
      on: {
        EXECUTOR_ACTIVITY: [
          { guard: 'activityMatches', actions: ['saveActivity', 'refreshView'] },
          { actions: 'rejectInput' },
        ],
        EXECUTOR_RETURNED: [
          { guard: 'resultMatches', target: 'AwaitingEvaluation', actions: ['saveWork', 'prepareEvaluation', 'refreshView'] },
          { actions: 'rejectInput' },
        ],
        RETURN_SAMPLE_WORK: { target: 'AwaitingEvaluation', actions: ['sampleWork', 'prepareEvaluation', 'refreshView'] },
      },
    },
    AwaitingEvaluation: {
      description: 'Inspect ExecutorOutput and EvaluatorInput side by side. Evaluator input carries canonical intent, graph, actual work and evidence; executor narrative stays in its separate return.',
    },
    CheckBinding: {
      always: [{ guard: 'evaluationMatches', target: 'ReadVerdict' }, { target: 'UnmatchedReceipt' }],
    },
    ReadVerdict: {
      always: [
        { guard: 'unfinished', target: 'UnfinishedEvaluation' },
        { guard: 'passed', target: 'Provisional' },
        { guard: 'failed', target: 'EvaluatedFail' },
        { target: 'NeedsReview' },
      ],
    },
    Provisional: { description: 'Inspect criterion evidence, intent/graph findings, proposals, and dependent-node eligibility in context.view.' },
    EvaluatedFail: { description: 'Work and findings remain visible. RETRY_WORK creates another attempt using cited findings against the same node.' },
    UnfinishedEvaluation: { description: 'RECOVER_EVALUATION requests evaluation of the preserved result, retaining earlier requests and receipts.' },
    UnmatchedReceipt: { description: 'The received receipt remains inspectable; it does not establish evaluation of this work.' },
    NeedsReview: { description: 'Evaluator requests human judgment; its report and proposals remain evidence.' },
    ReadDecision: { always: [{ guard: 'accepted', target: 'Accepted' }, { target: 'Rejected' }] },
    Accepted: { description: 'Separate human decision. Evaluation status remains separately visible in context.view.' },
    Rejected: { description: 'Separate human rejection. Work and evaluator reports remain inspectable.' },
  },
});

export const exampleEvents: Event[] = [
  { type: 'RUN_PASS' },
  { type: 'RETURN_SAMPLE_WORK' },
  { type: 'RETURN_SAMPLE_EVALUATION' },
  { type: 'HUMAN_ACCEPTED' },
];
