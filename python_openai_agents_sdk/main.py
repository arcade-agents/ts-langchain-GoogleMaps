from agents import (Agent, Runner, AgentHooks, Tool, RunContextWrapper,
                    TResponseInputItem,)
from functools import partial
from arcadepy import AsyncArcade
from agents_arcade import get_arcade_tools
from typing import Any
from human_in_the_loop import (UserDeniedToolCall,
                               confirm_tool_usage,
                               auth_tool)

import globals


class CustomAgentHooks(AgentHooks):
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name

    async def on_start(self,
                       context: RunContextWrapper,
                       agent: Agent) -> None:
        self.event_counter += 1
        print(f"### ({self.display_name}) {
              self.event_counter}: Agent {agent.name} started")

    async def on_end(self,
                     context: RunContextWrapper,
                     agent: Agent,
                     output: Any) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {
                # agent.name} ended with output {output}"
                agent.name} ended"
        )

    async def on_handoff(self,
                         context: RunContextWrapper,
                         agent: Agent,
                         source: Agent) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {
                source.name} handed off to {agent.name}"
        )

    async def on_tool_start(self,
                            context: RunContextWrapper,
                            agent: Agent,
                            tool: Tool) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}:"
            f" Agent {agent.name} started tool {tool.name}"
            f" with context: {context.context}"
        )

    async def on_tool_end(self,
                          context: RunContextWrapper,
                          agent: Agent,
                          tool: Tool,
                          result: str) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {
                # agent.name} ended tool {tool.name} with result {result}"
                agent.name} ended tool {tool.name}"
        )


async def main():

    context = {
        "user_id": os.getenv("ARCADE_USER_ID"),
    }

    client = AsyncArcade()

    arcade_tools = await get_arcade_tools(
        client, toolkits=["GoogleMaps"]
    )

    for tool in arcade_tools:
        # - human in the loop
        if tool.name in ENFORCE_HUMAN_CONFIRMATION:
            tool.on_invoke_tool = partial(
                confirm_tool_usage,
                tool_name=tool.name,
                callback=tool.on_invoke_tool,
            )
        # - auth
        await auth_tool(client, tool.name, user_id=context["user_id"])

    agent = Agent(
        name="",
        instructions="## Introduction
Welcome to the AI Directions Agent! This agent is designed to provide you accurate directions using Google Maps by either entering addresses or geographical coordinates. Whether you're planning a journey or just curious about travel routes, this agent can help streamline the process with detailed and efficient directions.

## Instructions
1. Users can request directions by providing either two physical addresses or by specifying the geographical coordinates (latitude and longitude) of both the origin and destination.
2. The agent can accept additional parameters such as language, country code, distance unit, and travel mode for a more tailored experience.
3. The agent will use Google Maps API tools to fetch the directions based on the provided information.
4. The response should always include key information such as the estimated travel distance and duration.

## Workflows
### Workflow 1: Get Directions Between Addresses
1. **Input:** User provides the origin and destination addresses.
2. **Use Tool:** `GoogleMaps_GetDirectionsBetweenAddresses`
   - Parameters: 
     - `origin_address` (user-provided origin)
     - `destination_address` (user-provided destination)
     - Optional parameters if provided: `language`, `country`, `distance_unit`, `travel_mode`
3. **Output:** Display directions, travel distance, and estimated time.

### Workflow 2: Get Directions Between Coordinates
1. **Input:** User provides the latitude and longitude for both the origin and destination.
2. **Use Tool:** `GoogleMaps_GetDirectionsBetweenCoordinates`
   - Parameters: 
     - `origin_latitude` (user-provided origin latitude)
     - `origin_longitude` (user-provided origin longitude)
     - `destination_latitude` (user-provided destination latitude)
     - `destination_longitude` (user-provided destination longitude)
     - Optional parameters if provided: `language`, `country`, `distance_unit`, `travel_mode`
3. **Output:** Display directions, travel distance, and estimated time.

### Additional Notes
- Ensure to validate user inputs for correct formats, especially for addresses and coordinates.
- Adapt the output to be concise yet informative, highlighting essential details for the user’s journey.",
        model=os.environ["OPENAI_MODEL"],
        tools=arcade_tools,
        hooks=CustomAgentHooks(display_name="")
    )

    # initialize the conversation
    history: list[TResponseInputItem] = []
    # run the loop!
    while True:
        prompt = input("You: ")
        if prompt.lower() == "exit":
            break
        history.append({"role": "user", "content": prompt})
        try:
            result = await Runner.run(
                starting_agent=agent,
                input=history,
                context=context
            )
            history = result.to_input_list()
            print(result.final_output)
        except UserDeniedToolCall as e:
            history.extend([
                {"role": "assistant",
                 "content": f"Please confirm the call to {e.tool_name}"},
                {"role": "user",
                 "content": "I changed my mind, please don't do it!"},
                {"role": "assistant",
                 "content": f"Sure, I cancelled the call to {e.tool_name}."
                 " What else can I do for you today?"
                 },
            ])
            print(history[-1]["content"])

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())