from arcadepy import AsyncArcade
from dotenv import load_dotenv
from google.adk import Agent, Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService, Session
from google_adk_arcade.tools import get_arcade_tools
from google.genai import types
from human_in_the_loop import auth_tool, confirm_tool_usage

import os

load_dotenv(override=True)


async def main():
    app_name = "my_agent"
    user_id = os.getenv("ARCADE_USER_ID")

    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    client = AsyncArcade()

    agent_tools = await get_arcade_tools(
        client, toolkits=["GoogleMaps"]
    )

    for tool in agent_tools:
        await auth_tool(client, tool_name=tool.name, user_id=user_id)

    agent = Agent(
        model=LiteLlm(model=f"openai/{os.environ["OPENAI_MODEL"]}"),
        name="google_agent",
        instruction="## Introduction
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
        description="An agent that uses GoogleMaps tools provided to perform any task",
        tools=agent_tools,
        before_tool_callback=[confirm_tool_usage],
    )

    session = await session_service.create_session(
        app_name=app_name, user_id=user_id, state={
            "user_id": user_id,
        }
    )
    runner = Runner(
        app_name=app_name,
        agent=agent,
        artifact_service=artifact_service,
        session_service=session_service,
    )

    async def run_prompt(session: Session, new_message: str):
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=new_message)]
        )
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.content.parts and event.content.parts[0].text:
                print(f'** {event.author}: {event.content.parts[0].text}')

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        await run_prompt(session, user_input)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())