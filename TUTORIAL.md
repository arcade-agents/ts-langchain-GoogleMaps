---
title: "Build a GoogleMaps agent with LangChain (TypeScript) and Arcade"
slug: "ts-langchain-GoogleMaps"
framework: "langchain-ts"
language: "typescript"
toolkits: ["GoogleMaps"]
tools: []
difficulty: "beginner"
generated_at: "2026-03-12T01:34:35Z"
source_template: "ts_langchain"
agent_repo: ""
tags:
  - "langchain"
  - "typescript"
  - "googlemaps"
---

# Build a GoogleMaps agent with LangChain (TypeScript) and Arcade

In this tutorial you'll build an AI agent using [LangChain](https://js.langchain.com/) with [LangGraph](https://langchain-ai.github.io/langgraphjs/) in TypeScript and [Arcade](https://arcade.dev) that can interact with GoogleMaps tools — with built-in authorization and human-in-the-loop support.

## Prerequisites

- The [Bun](https://bun.com) runtime
- An [Arcade](https://arcade.dev) account and API key
- An OpenAI API key

## Project Setup

First, create a directory for this project, and install all the required dependencies:

````bash
mkdir googlemaps-agent && cd googlemaps-agent
bun install @arcadeai/arcadejs @langchain/langgraph @langchain/core langchain chalk
````

## Start the agent script

Create a `main.ts` script, and import all the packages and libraries. Imports from 
the `"./tools"` package may give errors in your IDE now, but don't worry about those
for now, you will write that helper package later.

````typescript
"use strict";
import { getTools, confirm, arcade } from "./tools";
import { createAgent } from "langchain";
import {
  Command,
  MemorySaver,
  type Interrupt,
} from "@langchain/langgraph";
import chalk from "chalk";
import * as readline from "node:readline/promises";
````

## Configuration

In `main.ts`, configure your agent's toolkits, system prompt, and model. Notice
how the system prompt tells the agent how to navigate different scenarios and
how to combine tool usage in specific ways. This prompt engineering is important
to build effective agents. In fact, the more agentic your application, the more
relevant the system prompt to truly make the agent useful and effective at
using the tools at its disposal.

````typescript
// configure your own values to customize your agent

// The Arcade User ID identifies who is authorizing each service.
const arcadeUserID = process.env.ARCADE_USER_ID;
if (!arcadeUserID) {
  throw new Error("Missing ARCADE_USER_ID. Add it to your .env file.");
}
// This determines which MCP server is providing the tools, you can customize this to make a Slack agent, or Notion agent, etc.
// all tools from each of these MCP servers will be retrieved from arcade
const toolkits=['GoogleMaps'];
// This determines isolated tools that will be
const isolatedTools=[];
// This determines the maximum number of tool definitions Arcade will return
const toolLimit = 100;
// This prompt defines the behavior of the agent.
const systemPrompt = "Below is a ready-to-use ReAct-style system prompt for an AI agent that has access to the two Google Maps tools (GetDirectionsBetweenAddresses and GetDirectionsBetweenCoordinates). It instructs the agent how to behave, when and how to call tools, how to reason and format actions/answers, how to handle errors and ambiguities, and contains concrete workflows (sequences of tool use) for common tasks.\n\nUse this prompt as the agent\u0027s system instruction.\n\n---\n# Agent Prompt \u2014 Google Maps Directions ReAct Agent\n\nIntroduction\n------------\nYou are an intelligent ReAct-style routing assistant that provides driving/walking/transit/cycling directions and route summaries by calling the available Google Maps direction tools. Your job is to understand user requests about directions, choose the correct tool and parameters, call the tool(s) as needed, interpret the results, and present clear, actionable directions and summaries to the user.\n\nInstructions\n------------\n- Follow the ReAct pattern: think (internally) and then produce explicit actions when calling tools. For every tool call, write a brief Thought and then an Action block that specifies the tool name and the exact parameters.\n- Use the correct tool based on the type of origin/destination the user provides:\n  - If the user gives street addresses or place names, use GoogleMaps_GetDirectionsBetweenAddresses.\n  - If the user gives lat/lon coordinates, use GoogleMaps_GetDirectionsBetweenCoordinates.\n  - If the user gives mixed types (address + coordinates), call the appropriate tool for that segment. If a single tool cannot handle a multi-stop route, compute the route segment-by-segment by calling the appropriate tool for each consecutive pair.\n- Validate and normalize inputs before calling tools:\n  - For addresses: confirm there are enough details (street/city/region or a recognizable place name). If ambiguous or incomplete, ask a clarifying question.\n  - For coordinates: confirm they are numeric latitude/longitude in decimal degrees. If user-provided values do not parse, ask for correction.\n- Use optional parameters when supplied by the user:\n  - language: two-letter code (e.g., \"en\", \"es\").\n  - country: two-letter country code to help disambiguate addresses when requested (e.g., \"US\", \"GB\").\n  - distance_unit: pass user preference (KM or MILES). If absent, default is KM.\n  - travel_mode: one of driving/walking/bicycling/transit or \"BEST\". If absent, default is BEST.\n- Always include travel_mode and distance_unit in tool calls when the user explicitly requests them.\n- For multi-modal comparisons (e.g., \"show me driving vs public transit\"), call the same origin/destination with different travel_mode values and present a clear comparison table or bullet list of times and distances.\n- For multi-stop trips (more than two stops): call the tool for each leg (stop_i -\u003e stop_{i+1}) and aggregate distances, durations, and step-by-step instructions. Label each leg clearly.\n- Provide user-friendly final responses including:\n  - Short summary (total distance and duration).\n  - Turn-by-turn or step-by-step directions (or summarized steps if the route has many steps).\n  - Route warnings or constraints (e.g., ferries, tolls, departure times for transit) if provided by the tool or implied by the travel_mode.\n  - Clear indication of which travel mode and units were used.\n- If the tool returns multiple alternative routes, present the best route (shortest time by default) and optionally summarize up to 2 alternatives with their differences (time/distance).\n- If the tool indicates an error (no route found, invalid input, quota limit), do not invent results. Report the error and either ask for clarification or offer alternatives.\n- Respect user privacy and safety: never request or reveal sensitive personal information beyond what is necessary for routing (e.g., don\u0027t ask for social security, payment details, or other PII).\n- If the user asks for estimated arrival time, request a departure time if not provided, or use the user\u0027s stated departure time. If the user asks \"now\", compute ETA by adding travel duration to current time (note: if you do not have current time, ask the user to confirm departure time).\n- When you call a tool, include the exact parameters in the Action block. After receiving the observation (tool result), analyze it and present a clear, final answer to the user.\n\nReAct Action/Response Format\n----------------------------\nFollow this structured pattern when interacting (examples below). Use these labels verbatim so logs are consistent:\n\nThought: (short internal reasoning \u2014 one sentence)\nAction: \u003cToolName\u003e\nAction Input: { JSON-like parameters for the tool call }\n\nObservation: (tool response \u2014 provided by the tool)\nThought: (one-sentence follow-up if needed)\nFinal Answer: (the user-facing result / summary / question)\n\nExample tool-call snippets (do not run them now; these are examples of formatting)\n```\nThought: The user provided full addresses, so I\u0027ll call the address-to-address tool.\nAction: GoogleMaps_GetDirectionsBetweenAddresses\nAction Input: {\n  \"origin_address\": \"1600 Amphitheatre Parkway, Mountain View, CA\",\n  \"destination_address\": \"1 Infinite Loop, Cupertino, CA\",\n  \"language\": \"en\",\n  \"country\": \"US\",\n  \"distance_unit\": \"GoogleMapsDistanceUnit.KM\",\n  \"travel_mode\": \"GoogleMapsTravelMode.DRIVING\"\n}\n```\n\n```\nThought: The user provided coordinates; call the coordinates-to-coordinates tool.\nAction: GoogleMaps_GetDirectionsBetweenCoordinates\nAction Input: {\n  \"origin_latitude\": \"40.7128\",\n  \"origin_longitude\": \"-74.0060\",\n  \"destination_latitude\": \"40.7580\",\n  \"destination_longitude\": \"-73.9855\",\n  \"language\": \"en\",\n  \"distance_unit\": \"GoogleMapsDistanceUnit.MILES\",\n  \"travel_mode\": \"GoogleMapsTravelMode.WALKING\"\n}\n```\n\nWorkflows\n---------\nBelow are common workflows and the exact sequence of actions (tools) to use in each. For each workflow, the agent should validate inputs first, ask clarifying questions when needed, then run the described sequence.\n\n1) Basic route: Address -\u003e Address\n- When: user supplies both origin and destination as addresses/place names.\n- Sequence:\n  - Validate addresses (ask clarifying question if ambiguous).\n  - Call GoogleMaps_GetDirectionsBetweenAddresses once with language/country/distance_unit/travel_mode as provided or defaults.\n  - Parse tool output and present summary + step-by-step directions.\n- Example:\n  - Action: GoogleMaps_GetDirectionsBetweenAddresses {...}\n\n2) Basic route: Coordinates -\u003e Coordinates\n- When: user supplies both origin and destination as lat/lon coordinates.\n- Sequence:\n  - Validate numeric coordinates.\n  - Call GoogleMaps_GetDirectionsBetweenCoordinates once with provided or default optional parameters.\n  - Present summary + steps.\n- Example:\n  - Action: GoogleMaps_GetDirectionsBetweenCoordinates {...}\n\n3) Mixed-type single-leg route (Address -\u003e Coordinates or Coordinates -\u003e Address)\n- When: origin and destination are of different types.\n- Sequence:\n  - Validate both inputs.\n  - Use the appropriate single tool for that origin/destination pair (addresses -\u003e addresses or coordinates -\u003e coordinates). If one side is an address and the tool requires both addresses, convert the coordinate into a string form \"lat,lon\" if the address-based tool can accept it; if not, call the coordinates-based tool for the pair by extracting both as coordinates (ask user to supply missing coordinates or address as needed).\n  - If conversion is ambiguous, ask the user to provide consistent types.\n- Note: If the system environment expects strict types, prefer GoogleMaps_GetDirectionsBetweenCoordinates when either endpoint is coordinates.\n\n4) Multi-stop route (A -\u003e B -\u003e C -\u003e ... -\u003e N)\n- When: user gives multiple waypoints/stops.\n- Sequence:\n  - Validate each stop type. Normalize each stop into the appropriate form.\n  - For each consecutive pair (stop_i -\u003e stop_{i+1}), call the appropriate tool (addresses tool if both are addresses, coordinates tool if both are coordinates).\n  - Aggregate: sum distances and durations, concatenate step-by-step instructions labeling legs.\n  - Present overall totals, plus per-leg details.\n- Example:\n  - Action: GoogleMaps_GetDirectionsBetweenAddresses {origin: A, destination: B, ...}\n  - Observation -\u003e parse -\u003e then\n  - Action: GoogleMaps_GetDirectionsBetweenAddresses {origin: B, destination: C, ...}\n  - etc.\n\n5) Mode comparison (e.g., driving vs transit vs walking)\n- When: user requests to compare travel modes.\n- Sequence:\n  - Validate origin/destination inputs.\n  - For each requested travel mode, call the same directions tool with travel_mode set accordingly (use the address tool if addresses; coordinates tool for coordinates).\n  - Present a side-by-side comparison of total time, distance, and notable route differences (e.g., transfers for transit).\n- Example:\n  - Action: GoogleMaps_GetDirectionsBetweenAddresses {..., \"travel_mode\": \"GoogleMapsTravelMode.DRIVING\"}\n  - Action: GoogleMaps_GetDirectionsBetweenAddresses {..., \"travel_mode\": \"GoogleMapsTravelMode.TRANSIT\"}\n\n6) Route with departure/arrival time considerations (transit or ETA)\n- When: user provides departure_time or asks for ETA at a specific arrival_time.\n- Sequence:\n  - Ask for explicit departure/arrival time if not provided.\n  - Use the tool (if tool supports time-based queries via parameters \u2014 if not supported, estimate based on current/default conditions and inform the user about limits).\n  - If tool returns schedule-based results, include expected departure/arrival times and transfers.\n- Note: If the API/tool available does not accept a departure_time parameter, explicitly state this limitation to the user and offer alternatives.\n\n7) Fallbacks and errors\n- When tool returns \"no route\" or an error:\n  - Re-check inputs and ask the user to clarify ambiguous addresses or provide coordinates.\n  - If failure persists, offer alternatives (e.g., \"I can\u0027t find a route \u2014 would you like me to search for nearby transit stations or show an approximate straight-line distance?\").\n- When tool returns multiple routes:\n  - Choose the fastest by default; offer the user the alternatives if they want to see them.\n\nOutput formatting \u0026 final answer\n--------------------------------\n- Final Answer must be user-facing and concise:\n  - Start with a one-line summary: total travel mode, total time, total distance (with units).\n  - Provide a numbered list of major steps or per-leg summaries. If the route includes many steps, give the top 5 important maneuvers and offer to show full turn-by-turn instructions.\n  - If performing comparisons, show a short bullets or table-like listing of times/distances per mode.\n- Cite the tool call(s) used by listing the actions made (tool names and parameters are not required verbatim in the final user message but you should reference that you retrieved live directions).\n- If you ask a question to clarify user input, keep it short and specific.\n\nExample full ReAct interaction (for agent logs)\n----------------------------------------------\nThought: The user wants driving directions between two addresses; ask no clarifying question because both addresses are complete.\nAction: GoogleMaps_GetDirectionsBetweenAddresses\nAction Input: {\n  \"origin_address\": \"1600 Amphitheatre Parkway, Mountain View, CA\",\n  \"destination_address\": \"1 Infinite Loop, Cupertino, CA\",\n  \"language\": \"en\",\n  \"country\": \"US\",\n  \"distance_unit\": \"GoogleMapsDistanceUnit.KM\",\n  \"travel_mode\": \"GoogleMapsTravelMode.DRIVING\"\n}\nObservation: { ...tool response... }\nThought: The route is 14.2 km and takes 20 minutes via Highway 85. Provide summary and steps.\nFinal Answer: Driving from 1600 Amphitheatre Pkwy to 1 Infinite Loop \u2014 14.2 km, ~20 minutes. 1) Head southeast on Amphitheatre Pkwy... [first 5 steps]. Want full turn-by-turn?\n\nNotes and best practices\n------------------------\n- Prefer addresses when possible (they are easier for users) but support coordinates.\n- Always confirm ambiguous inputs (e.g., \"Paris\" \u2014 ask which country).\n- Use user-specified language/country to shape tool calls and output language.\n- If the user requests that directions be optimized (shortest vs fastest), honor that preference by selecting the appropriate alternative route from the tool output or by calling tool with an appropriate parameter if available.\n- Keep responses concise and actionable. Offer to show more detail (full step list, map link, or alternative routes).\n\nEnd of prompt\n-----------\n\nUse this prompt to run the ReAct agent. Adjust language/country defaults only if the user explicitly requests different defaults.";
// This determines which LLM will be used inside the agent
const agentModel = process.env.OPENAI_MODEL;
if (!agentModel) {
  throw new Error("Missing OPENAI_MODEL. Add it to your .env file.");
}
// This allows LangChain to retain the context of the session
const threadID = "1";
````

Set the following environment variables in a `.env` file:

````bash
ARCADE_API_KEY=your-arcade-api-key
ARCADE_USER_ID=your-arcade-user-id
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5-mini
````

## Implementing the `tools.ts` module

The `tools.ts` module fetches Arcade tool definitions and converts them to LangChain-compatible tools using Arcade's Zod schema conversion:

### Create the file and import the dependencies

Create a `tools.ts` file, and add import the following. These will allow you to build the helper functions needed to convert Arcade tool definitions into a format that LangChain can execute. Here, you also define which tools will require human-in-the-loop confirmation. This is very useful for tools that may have dangerous or undesired side-effects if the LLM hallucinates the values in the parameters. You will implement the helper functions to require human approval in this module.

````typescript
import { Arcade } from "@arcadeai/arcadejs";
import {
  type ToolExecuteFunctionFactoryInput,
  type ZodTool,
  executeZodTool,
  isAuthorizationRequiredError,
  toZod,
} from "@arcadeai/arcadejs/lib/index";
import { type ToolExecuteFunction } from "@arcadeai/arcadejs/lib/zod/types";
import { tool } from "langchain";
import {
  interrupt,
} from "@langchain/langgraph";
import readline from "node:readline/promises";

// This determines which tools require human in the loop approval to run
const TOOLS_WITH_APPROVAL = [];
````

### Create a confirmation helper for human in the loop

The first helper that you will write is the `confirm` function, which asks a yes or no question to the user, and returns `true` if theuser replied with `"yes"` and `false` otherwise.

````typescript
// Prompt user for yes/no confirmation
export async function confirm(question: string, rl?: readline.Interface): Promise<boolean> {
  let shouldClose = false;
  let interface_ = rl;

  if (!interface_) {
      interface_ = readline.createInterface({
          input: process.stdin,
          output: process.stdout,
      });
      shouldClose = true;
  }

  const answer = await interface_.question(`${question} (y/n): `);

  if (shouldClose) {
      interface_.close();
  }

  return ["y", "yes"].includes(answer.trim().toLowerCase());
}
````

Tools that require authorization trigger a LangGraph interrupt, which pauses execution until the user completes authorization in their browser.

### Create the execution helper

This is a wrapper around the `executeZodTool` function. Before you execute the tool, however, there are two logical checks to be made:

1. First, if the tool the agent wants to invoke is included in the `TOOLS_WITH_APPROVAL` variable, human-in-the-loop is enforced by calling `interrupt` and passing the necessary data to call the `confirm` helper. LangChain will surface that `interrupt` to the agentic loop, and you will be required to "resolve" the interrupt later on. For now, you can assume that the reponse of the `interrupt` will have enough information to decide whether to execute the tool or not, depending on the human's reponse.
2. Second, if the tool was approved by the human, but it doesn't have the authorization of the integration to run, then you need to present an URL to the user so they can authorize the OAuth flow for this operation. For this, an execution is attempted, that may fail to run if the user is not authorized. When it fails, you interrupt the flow and send the authorization request for the harness to handle. If the user authorizes the tool, the harness will reply with an `{authorized: true}` object, and the system will retry the tool call without interrupting the flow.

````typescript
export function executeOrInterruptTool({
  zodToolSchema,
  toolDefinition,
  client,
  userId,
}: ToolExecuteFunctionFactoryInput): ToolExecuteFunction<any> {
  const { name: toolName } = zodToolSchema;

  return async (input: unknown) => {
    try {

      // If the tool is on the list that enforces human in the loop, we interrupt the flow and ask the user to authorize the tool

      if (TOOLS_WITH_APPROVAL.includes(toolName)) {
        const hitl_response = interrupt({
          authorization_required: false,
          hitl_required: true,
          tool_name: toolName,
          input: input,
        });

        if (!hitl_response.authorized) {
          // If the user didn't approve the tool call, we throw an error, which will be handled by LangChain
          throw new Error(
            `Human in the loop required for tool call ${toolName}, but user didn't approve.`
          );
        }
      }

      // Try to execute the tool
      const result = await executeZodTool({
        zodToolSchema,
        toolDefinition,
        client,
        userId,
      })(input);
      return result;
    } catch (error) {
      // If the tool requires authorization, we interrupt the flow and ask the user to authorize the tool
      if (error instanceof Error && isAuthorizationRequiredError(error)) {
        const response = await client.tools.authorize({
          tool_name: toolName,
          user_id: userId,
        });

        // We interrupt the flow here, and pass everything the handler needs to get the user's authorization
        const interrupt_response = interrupt({
          authorization_required: true,
          authorization_response: response,
          tool_name: toolName,
          url: response.url ?? "",
        });

        // If the user authorized the tool, we retry the tool call without interrupting the flow
        if (interrupt_response.authorized) {
          const result = await executeZodTool({
            zodToolSchema,
            toolDefinition,
            client,
            userId,
          })(input);
          return result;
        } else {
          // If the user didn't authorize the tool, we throw an error, which will be handled by LangChain
          throw new Error(
            `Authorization required for tool call ${toolName}, but user didn't authorize.`
          );
        }
      }
      throw error;
    }
  };
}
````

### Create the tool retrieval helper

The last helper function of this module is the `getTools` helper. This function will take the configurations you defined in the `main.ts` file, and retrieve all of the configured tool definitions from Arcade. Those definitions will then be converted to LangGraph `Function` tools, and will be returned in a format that LangChain can present to the LLM so it can use the tools and pass the arguments correctly. You will pass the `executeOrInterruptTool` helper you wrote in the previous section so all the bindings to the human-in-the-loop and auth handling are programmed when LancChain invokes a tool.


````typescript
// Initialize the Arcade client
export const arcade = new Arcade();

export type GetToolsProps = {
  arcade: Arcade;
  toolkits?: string[];
  tools?: string[];
  userId: string;
  limit?: number;
}


export async function getTools({
  arcade,
  toolkits = [],
  tools = [],
  userId,
  limit = 100,
}: GetToolsProps) {

  if (toolkits.length === 0 && tools.length === 0) {
      throw new Error("At least one tool or toolkit must be provided");
  }

  // Todo(Mateo): Add pagination support
  const from_toolkits = await Promise.all(toolkits.map(async (tkitName) => {
      const definitions = await arcade.tools.list({
          toolkit: tkitName,
          limit: limit
      });
      return definitions.items;
  }));

  const from_tools = await Promise.all(tools.map(async (toolName) => {
      return await arcade.tools.get(toolName);
  }));

  const all_tools = [...from_toolkits.flat(), ...from_tools];
  const unique_tools = Array.from(
      new Map(all_tools.map(tool => [tool.qualified_name, tool])).values()
  );

  const arcadeTools = toZod({
    tools: unique_tools,
    client: arcade,
    executeFactory: executeOrInterruptTool,
    userId: userId,
  });

  // Convert Arcade tools to LangGraph tools
  const langchainTools = arcadeTools.map(({ name, description, execute, parameters }) =>
    (tool as Function)(execute, {
      name,
      description,
      schema: parameters,
    })
  );

  return langchainTools;
}
````

## Building the Agent

Back on the `main.ts` file, you can now call the helper functions you wrote to build the agent.

### Retrieve the configured tools

Use the `getTools` helper you wrote to retrieve the tools from Arcade in LangChain format:

````typescript
const tools = await getTools({
  arcade,
  toolkits: toolkits,
  tools: isolatedTools,
  userId: arcadeUserID,
  limit: toolLimit,
});
````

### Write an interrupt handler

When LangChain is interrupted, it will emit an event in the stream that you will need to handle and resolve based on the user's behavior. For a human-in-the-loop interrupt, you will call the `confirm` helper you wrote earlier, and indicate to the harness whether the human approved the specific tool call or not. For an auth interrupt, you will present the OAuth URL to the user, and wait for them to finishe the OAuth dance before resolving the interrupt with `{authorized: true}` or `{authorized: false}` if an error occurred:

````typescript
async function handleInterrupt(
  interrupt: Interrupt,
  rl: readline.Interface
): Promise<{ authorized: boolean }> {
  const value = interrupt.value;
  const authorization_required = value.authorization_required;
  const hitl_required = value.hitl_required;
  if (authorization_required) {
    const tool_name = value.tool_name;
    const authorization_response = value.authorization_response;
    console.log("⚙️: Authorization required for tool call", tool_name);
    console.log(
      "⚙️: Please authorize in your browser",
      authorization_response.url
    );
    console.log("⚙️: Waiting for you to complete authorization...");
    try {
      await arcade.auth.waitForCompletion(authorization_response.id);
      console.log("⚙️: Authorization granted. Resuming execution...");
      return { authorized: true };
    } catch (error) {
      console.error("⚙️: Error waiting for authorization to complete:", error);
      return { authorized: false };
    }
  } else if (hitl_required) {
    console.log("⚙️: Human in the loop required for tool call", value.tool_name);
    console.log("⚙️: Please approve the tool call", value.input);
    const approved = await confirm("Do you approve this tool call?", rl);
    return { authorized: approved };
  }
  return { authorized: false };
}
````

### Create an Agent instance

Here you create the agent using the `createAgent` function. You pass the system prompt, the model, the tools, and the checkpointer. When the agent runs, it will automatically use the helper function you wrote earlier to handle tool calls and authorization requests.

````typescript
const agent = createAgent({
  systemPrompt: systemPrompt,
  model: agentModel,
  tools: tools,
  checkpointer: new MemorySaver(),
});
````

### Write the invoke helper

This last helper function handles the streaming of the agent’s response, and captures the interrupts. When the system detects an interrupt, it adds the interrupt to the `interrupts` array, and the flow interrupts. If there are no interrupts, it will just stream the agent’s to your console.

````typescript
async function streamAgent(
  agent: any,
  input: any,
  config: any
): Promise<Interrupt[]> {
  const stream = await agent.stream(input, {
    ...config,
    streamMode: "updates",
  });
  const interrupts: Interrupt[] = [];

  for await (const chunk of stream) {
    if (chunk.__interrupt__) {
      interrupts.push(...(chunk.__interrupt__ as Interrupt[]));
      continue;
    }
    for (const update of Object.values(chunk)) {
      for (const msg of (update as any)?.messages ?? []) {
        console.log("🤖: ", msg.toFormattedString());
      }
    }
  }

  return interrupts;
}
````

### Write the main function

Finally, write the main function that will call the agent and handle the user input.

Here the `config` object configures the `thread_id`, which tells the agent to store the state of the conversation into that specific thread. Like any typical agent loop, you:

1. Capture the user input
2. Stream the agent's response
3. Handle any authorization interrupts
4. Resume the agent after authorization
5. Handle any errors
6. Exit the loop if the user wants to quit

````typescript
async function main() {
  const config = { configurable: { thread_id: threadID } };
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  console.log(chalk.green("Welcome to the chatbot! Type 'exit' to quit."));
  while (true) {
    const input = await rl.question("> ");
    if (input.toLowerCase() === "exit") {
      break;
    }
    rl.pause();

    try {
      let agentInput: any = {
        messages: [{ role: "user", content: input }],
      };

      // Loop until no more interrupts
      while (true) {
        const interrupts = await streamAgent(agent, agentInput, config);

        if (interrupts.length === 0) {
          break; // No more interrupts, we're done
        }

        // Handle all interrupts
        const decisions: any[] = [];
        for (const interrupt of interrupts) {
          decisions.push(await handleInterrupt(interrupt, rl));
        }

        // Resume with decisions, then loop to check for more interrupts
        // Pass single decision directly, or array for multiple interrupts
        agentInput = new Command({ resume: decisions.length === 1 ? decisions[0] : decisions });
      }
    } catch (error) {
      console.error(error);
    }

    rl.resume();
  }
  console.log(chalk.red("👋 Bye..."));
  process.exit(0);
}

// Run the main function
main().catch((err) => console.error(err));
````

## Running the Agent

### Run the agent

```bash
bun run main.ts
```

You should see the agent responding to your prompts like any model, as well as handling any tool calls and authorization requests.

## Next Steps

- Clone the [repository](https://github.com/arcade-agents/ts-langchain-GoogleMaps) and run it
- Add more toolkits to the `toolkits` array to expand capabilities
- Customize the `systemPrompt` to specialize the agent's behavior
- Explore the [Arcade documentation](https://docs.arcade.dev) for available toolkits

