import { agent, defineWorkflow } from "@osolmaz/pi-workflows";

// One input, one agent step, one validated output, then completion.
export default defineWorkflow({
  name: "hello",
  startAt: "greet",
  maxSteps: 1,
  nodes: {
    greet: agent({
      prompt: ({ input }) =>
        `Return a greeting for this name: ${JSON.stringify((input as { task?: string }).task || "world")}. Use exactly "Hello, <name>!" as the greeting.`,
      expectedOutput: '{ "greeting": "Hello, <name>!" }',
      allowedTools: [],
      timeoutMs: 60_000,
      validate: (output, { input }) => {
        const value = output as { greeting?: unknown };
        const name = (input as { task?: string }).task || "world";
        if (!value || typeof value.greeting !== "string" ||
            value.greeting !== `Hello, ${name}!`) {
          throw new Error('Expected { "greeting": "Hello, <name>!" }.');
        }
        return { greeting: value.greeting };
      },
    }),
  },
  edges: [],
});
