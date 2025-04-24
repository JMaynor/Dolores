# Summary

Discord bot named Dolores for rolling dice, playing audio, and a number of other helper functions. She was initially created to help facilitiate playing tabletop games over Discord.

Dolores is generally just a python program. I run her in a Docker container, allows for easier updating. An example `docker-compose.yml` file is included in the project, assuming the user wants to make use of all functionality.

> Note: Dolores is largely a personal project created for a few small Discord servers. So there's a number of features or peculiarities that specifically deal with things unique to what I want her to do. Should still be useful in a broader more generalized context, but I will work over time to make her less specific. Or at least make her uses more configurable.

## Config

Dolores runs using a number of environment variables for API keys and settings. Not all are required for core functionality. Each cog has a corresponding environment variable to turn it on or off. Will determine whether the cog is loaded when Dolores is run. If a cog isn't loaded, none of the environment variables that are associated with that module are required.

The only explicitly required environment variable is `DISCORD_API_KEY`.

Env vars can be provided via a `.env` file in the main directory, if desired. Useful for testing locally. If created and filled out, Dolores can thus be ran with command `docker compose --env-file .env up -d --remove-orphans`.

| Required by Which Module | Env Var Name | Description |
| --- | --- | --- |
|  |  |  |
| Base | DISCORD_API_KEY | The main API key for the bot. |
| Base | AUDIO_ENABLED | Enables audio cog, when set as true |
| Base | SCHEDULING_ENABLED | Enables scheduling cog, when set as true |
| Base | GENERATION_ENABLED | Enables URL sumamrization, LLM replies, image generation. |
| Base | LOG_LEVEL | Level of logging. Dolores uses DEBUG, INFO, and ERROR. |
| Scheduling | NOTION_API_KEY | API Key for querying data from Notion |
| Scheduling | NOTION_VERSION | Version of Notion API used for querying. |
| Scheduling | NOTION_BASE_URL | Base URL of the Notion API, should be |
| Scheduling | NOTION_DATABASE_ID | ID for database where stream info is kept |
| Generation | OPENAI_API_KEY | API Key used for generating replies |
| Generation | LLM_MODEL | Which LLM model to use. |
| Generation | IMAGE_MODEL | Which image model to use. |
| Generation | IMAGE_STYLE | vivid or natural |
| Generation | MAX_TOKENS | Max number of tokens generated in LLM chat. |
| Generation | TEMPERATURE | Float value for temperature of LLM chat response. |
| Generation | TOP_P | Float value alternative to temperature with LLM chat. |
| Generation | FREQUENCY_PENALTY | Frequency penalty for LLM chat. |
| Generation | PRESENCE_PENALTY | Presence penalty for LLM chat. |

## Modules

Dolores' functionality is divided into several cogs modules. `dolores.py` handles main discord events and processing commands.

| Cog | Description |
| --- | ----------- |
| Rolling | Used to roll dice and for any other randomization-based tasks. |
| Audio | The audio module uses pomice/lavalink to stream audio. Uses a queue system. Largely a copy of the example bot given in pomice's documentation. |
| Scheduling | The scheduling module is used for tasks related to Notion. Pulling schedule in from a Notion database. |
| Generation | Module for text and image generation. Currently using chatGPT, but intent is to move to add ability to use self-hosted LLM. Should be able to choose between something the user is hosting or commercially available alternatives. Also handles simple randomized snarky replies. |

## Licensing

This project is licensed under the terms of the MIT license.
