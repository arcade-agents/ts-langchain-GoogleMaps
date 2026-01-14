# An agent that uses GoogleMaps tools provided to perform any task

## Purpose

## Introduction
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
- Adapt the output to be concise yet informative, highlighting essential details for the user’s journey.

## MCP Servers

The agent uses tools from these Arcade MCP Servers:

- GoogleMaps

## Getting Started

1. Install dependencies:
    ```bash
    bun install
    ```

2. Set your environment variables:

    Copy the `.env.example` file to create a new `.env` file, and fill in the environment variables.
    ```bash
    cp .env.example .env
    ```

3. Run the agent:
    ```bash
    bun run main.ts
    ```