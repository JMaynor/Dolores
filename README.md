# Summary

Discord bot named Dolores for rolling dice, playing audio, and a number of other helper functions. She was initially created to help facilitiate playing tabletop games over Discord.

Dolores can be run easily directly as a python program. Generally, I have her running as a Docker container, allows for easier updating. An example `compose.yml` layout is included below, assuming the user wants to make use of all functionality.

> Note: Dolores is largely a personal project created for a few small Discord servers. So there's a number of features or peculiarities that specifically deal with things unique to what I want her to do. Should still be useful in a broader more generalized context, but I will work over time to make her less specific. Or at least make her uses more configurable.

## Config

Dolores runs using a number of environment variables for API keys and settings. Not all are required for core functionality. Each cog has a corresponding environment variable to turn it on or off. Will determine whether the cog is loaded when Dolores is run. If a cog isn't loaded, none of the environment variables that are associated with that module are required.

The only explicitly required environment variable is `DISCORD_API_KEY`.

Env vars can be provided via a `.env` file in the main directory, if desired. Useful for testing locally.

| Required by Which Module | Env Var Name | Description |
| --- | --- | --- |
|  |  |  |
| Base | DISCORD_API_KEY | The main API key for the bot. |
| Base | AUDIO_ENABLED | Enables audio cog, when set as true |
| Base | SCHEDULING_ENABLED | Enables scheduling cog, when set as true |
| Base | TEXT_ENABLED |  |
| Base | LOG_LEVEL | Level of logging. Dolores uses DEBUG, INFO, and ERROR. |
| Scheduling | NOTION_API_KEY | API Key for querying data from Notion |
| Scheduling | NOTION_VERSION | Version of Notion API used for querying. |
| Scheduling | NOTION_BASE_URL | Base URL of the Notion API, should be |
| Scheduling | NOTION_DATABASE_ID | ID for database where stream info is kept |
| None | TWITCH_CLIENT_ID | Not yet used |
| None | TWITCH_CLIENT_SECRET | Not yet used |
| None | TWITCH_BASE_URL | Not yet used |
| None | TWITCH_BROADCASTER_ID | Not yet used |
| None | TWITCH_BROADCASTER_NAME | not yet used |
| Text | REPLY_METHOD | Method to use for generating a reply to user's message. At this point only 'openai' is supported. |
| Text | OPENAI_API_KEY | API Key used for generating replies |
| Text | OPENAI_MODEL | Which LLM model to use. |
| Text | MAX_TOKENS | Max number of tokens generated in LLM chat. |
| Text | TEMPERATURE | Float value for temperature of LLM chat response. |
| Text | TOP_P | Float value alternative to temperature with LLM chat. |
| Text | FREQUENCY_PENALTY | Frequency penalty for LLM chat. |
| Text | PRESENCE_PENALTY | Presence penalty for LLM chat. |
| Text | SMMRY_BASE_URL | base URL for the SMMRY API. |
| Text | SMMRY_API_KEY | API key for the SMMRY API |
| Text | SMMRY_QUOTE_AVOID | SMMRY boolean option on whether to avoid or include quotes in text that's summarized. Usually true. |
| Text | SMMRY_LENGTH | max number of sentences a summary should be. |
| Text | SMMRY_MIN_REDUCED_AMOUNT | Minium percentage a news article should be reduced by summarization to post it. |
| Text | NEWS_CHANNEL_ID | Not currently used, but was automatically summarizing articles posted into a particular discord channel. |

## Compose

Below is an example docker compose spec if using all functionality.

```yml
name: Dolores

services:
  dolores:
    image: exaltatus/dolores:latest
    container_name: dolores
    restart: unless-stopped
    volumes:
      - C:\{Docker folder}\Dolores:/home/dolores/config
  lavalink:
    image: ghcr.io/lavalink-devs/lavalink:4
    container_name: lavalink
    restart: unless-stopped
    environment:
      - _JAVA_OPTIONS=-Xmx6G
      - SERVER_PORT=2333
      - SERVER_ADDRESS=0.0.0.0
      - SERVER_HTTP2_ENABLED=true
      - LAVALINK_SERVER_PASSWORD=password
      - LAVALINK_SERVER_SOURCES_YOUTUBE=true
      - LAVALINK_SERVER_SOURCES_BANDCAMP=false
      - LAVALINK_SERVER_SOURCES_SOUNDCLOUD=false
      - LAVALINK_SERVER_SOURCES_TWITCH=false
      - LAVALINK_SERVER_SOURCES_VIMEO=false
      - LAVALINK_SERVER_SOURCES_HTTP=true
      - LAVALINK_SERVER_SOURCES_LOCAL=false
      - LAVALINK_PLUGINS_DIR=/opt/Lavalink/plugins/
    volumes:
      - C:\{Docker folder}\lavalink\plugins/:/opt/Lavalink/plugins/
    networks:
      - lavalink
    expose:
      - 2333
    ports:
      - "2333:2333"
```

## Modules

Dolores' functionality is divided into several cogs modules. `dolores.py` handles main discord events and processing commands.

| Cog | Description |
| --- | ----------- |
| Rolling | Used to roll dice and for any other randomization-based tasks. |
| Audio | The audio module uses pomice/lavalink to stream audio. Uses a queue system. Largely a copy of the example bot given in pomice's documentation. |
| Scheduling | The scheduling module is used for tasks related to Notion and Twitch. Pulling schedule in from a Notion database and posting to twitch schedule. |
| Text | Module for text generation. Currently using chatGPT, but intent is to move to add ability to use self-hosted LLM. Should be able to choose between something the user is hosting or commercially available alternatives. Also handles simple randomized snarky replies. |

## Licensing

This project is licensed under the terms of the MIT license.
