# Summary

Discord bot named Dolores for rolling dice and a number of other helper functions.

Dolores can be run easily directly as a python program, but she can also be ran within a Docker container, allowing for easier updating.

Note: Dolores requires a config.yml file with a bot API key and a couple other details to run. example_config.yml is included to show formatting. Config file is organized by service. The only heading explicitly required to run is the info under DISCORD

## Modules

Dolores' functionality is divided into several cogs modules. dolores.py handles discord events and processing commands.

### Rolling

The main module. Used to roll dice and for any other randomization-based tasks.

### Audio

The audio module uses yt-dlp to download videos and stream the audio into whichever channel the calling user is in.

### Scheduling

The scheduling module is used for tasks related to Notion and Twitch. Pulling schedule in from a Notion database and posting to twitch schedule.

### Text

Module for text generation. Currently using chatGPT, but intent is to move to add ability to use self-hosted LLM. Should be able to choose between something the user is hosting or commercially available alternatives. Also handles simple randomized snarky replies.
