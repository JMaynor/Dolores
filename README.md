# Summary

Discord bot named Dolores for rolling dice, playing audio, and a number of other helper functions. She was initially created to help facilitiate playing tabletop games over Discord.

Dolores can be run easily directly as a python program, but she can also be ran within a Docker container, allowing for easier updating. An example `compose.yml` layout is below, assuming the user wants to make use of the lavalink functionality.

> Note: Dolores is largely a personal project created for a few small Discord servers. So there's a number of features or peculiarities that specifically deal with things unique to what we want her to do. Should still be useful in a broader more generalized context, but I will work over time to make her less specific. Or at least make her uses more configurable.

## Config

Dolores requires a config.yml file with a bot API key and a couple other details to run. example_config.yml is included to show formatting. Config file is organized by service. The only heading explicitly required to run is the info under DISCORD.

> Note: Intention is to move all config to env vars so easier to deploy via a single compose spec. No need for the config file.

Below is an example docker compose spec.

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
