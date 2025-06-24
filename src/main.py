"""
Dolores is a chatbot that connects to a Discord server. Her primary use
is in being able to roll dice for players of a tabletop roleplaying game
but she is also capable of doing some basic audio things.
"""

import os
import re
from pathlib import Path

import hikari
import hikari.events.reaction_events
import lightbulb
from dotenv import load_dotenv

# Check if .env file present, if so load vars from it
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from src._logger import logger
from src.audio import music
from src.chat import chat

AUDIO_REQUIRED_VARS = ["LAVALINK_HOST", "LAVALINK_PORT", "LAVALINK_PASSWORD"]
# Chat also requires an API key, but the var name will be different
# depending on whatever service being used, so can't check for.
CHAT_REQUIRED_VARS = ["LLM_MODEL"]
IMAGES_REQUIRED_VARS = ["OPENAI_API_KEY", "IMAGE_MODEL"]
ROLLING_REQUIRED_VARS = []
SCHEDULING_REQUIRED_VARS = [
    "NOTION_BASE_URL",
    "NOTION_DATABASE_ID",
    "NOTION_API_KEY",
    "NOTION_VERSION",
]

bot = hikari.GatewayBot(intents=hikari.Intents.ALL, token=os.environ["DISCORD_API_KEY"])
client = lightbulb.client_from_app(bot)


def check_for_required_env_vars(vars: list[str]) -> bool:
    """
    Checks that the list of envvars provided are present in the environment.
    Returns True if all are present, False if any are missing.
    """
    missing_vars = [var for var in vars if not os.environ.get(var)]
    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        return False
    return True


async def handle_mention(message: hikari.Message):
    """
    handle_mention is a coroutine that handles the bot's response to being mentioned
    in a message. It will generate a reply to the message and send it to the channel
    where the message was posted.
    """
    message_content = message.content
    if message_content is None:
        return

    if chat_inst is None:
        return

    message_content = message_content.replace("@Dolores", "Dolores")
    message_content = message_content.replace("@everyone", "everyone")
    message_content = message_content.replace("@Testie", "Testie")

    # Remove invalid characters from author name
    author = message.author.display_name
    if author:
        author = re.sub(r"[^a-zA-Z0-9_]", "", author)
        author = author.replace(" ", "_")
    else:
        author = "discord_user"  # Fallback to a default name

    logger.info(f"Generating reply to following message: {message_content}")
    reply = await chat_inst.generate_reply(author, message_content)

    if reply != "":
        await message.respond(reply, reply=message)


async def handle_question(message) -> None:
    """
    When someone reacts with a question mark to a message, Dolores will attempt
    to explain the contents of the message in an informative simpler way.
    Calls generate_explanation in the generation module.
    """
    message_content = message.content
    if message_content is None:
        return

    if chat_inst is None:
        return

    # Remove invalid characters from author name
    author = message.author.display_name
    if author:
        author = re.sub(r"[^a-zA-Z0-9_]", "", author)
        author = author.replace(" ", "_")
    else:
        author = "discord_user"  # Fallback to a default name

    logger.info(f"Generating explanation for message: {message_content}")

    explanation = chat_inst.generate_explanation(author, message_content)

    if explanation:
        await message.respond(explanation, reply=message)


# ---------------------------------------------------------------------------
# Discord Events
# ---------------------------------------------------------------------------


@bot.listen()
async def on_ready(event: hikari.StartedEvent) -> None:
    """
    on_ready gets called when the bot starts up or potentially when restarts
    in event of a reconnection.
    """
    logger.info("Dolores has connected to Discord.")


@bot.listen()
async def on_reaction_add(event: hikari.ReactionAddEvent):
    """
    on_reaction_add is a base function for handling when a reaction is added
    to a message. Currently used to check for question mark reaction
    """
    if event.is_for_emoji("❓") or event.is_for_emoji("❔"):
        await handle_question(event.message_id)


@bot.listen()
async def on_message(event: hikari.MessageCreateEvent):
    """
    on_message is the base function for handling any message that is sent on the server.
    There are a couple special cases that are handled here
    """

    if not event.is_human:
        return

    me = bot.get_me()

    if (
        me.id in event.message.user_mentions_ids  # type: ignore
        and "@everyone" not in event.message.content  # type: ignore
    ):
        logger.info(f"Message: {event.message}")
        await handle_mention(event.message)
        return


@bot.listen(hikari.StartingEvent)
async def on_starting(_: hikari.StartingEvent) -> None:
    """
    Called while bot is starting up. Adds commands to it. Any other initialization-related
    things that need to be done before the bot connects to discord should be done here.
    """
    if check_for_required_env_vars(AUDIO_REQUIRED_VARS):
        logger.info("Loading audio module")
        # await client.load_extensions("audio")
        client.register(music)
    if check_for_required_env_vars(IMAGES_REQUIRED_VARS):
        logger.info("Loading images module")
        await client.load_extensions("images")
    if check_for_required_env_vars(ROLLING_REQUIRED_VARS):
        logger.info("Loading rolling module")
        await client.load_extensions("rolling")
    if check_for_required_env_vars(SCHEDULING_REQUIRED_VARS):
        logger.info("Loading scheduling module")
        await client.load_extensions("scheduling")

    await client.start()


@bot.listen()
async def on_voice_state_update(event: hikari.VoiceStateUpdateEvent):
    """
    Handle voice state updates for lavalink integration.
    This is required for lavalink to know about voice connections.
    """
    from src.lavaclient import music_client

    if music_client and music_client.lavalink:
        await music_client.lavalink.voice_update_handler(event)  # type: ignore


@bot.listen()
async def on_voice_server_update(event: hikari.VoiceServerUpdateEvent):
    """
    Handle voice server updates for lavalink integration.
    This is required for lavalink to connect to Discord's voice servers.
    """
    from src.lavaclient import music_client

    if music_client and music_client.lavalink:
        await music_client.lavalink.voice_update_handler(event)  # type: ignore


if __name__ == "__main__":
    """
    Main program entry point
    """
    if check_for_required_env_vars(CHAT_REQUIRED_VARS):
        chat_inst = chat()
    else:
        chat_inst = None
    bot.run()
