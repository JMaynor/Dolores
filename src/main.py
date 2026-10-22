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
from pydantic_ai import BinaryImage

# Check if .env file present, if so load vars from it
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from src._logger import logger
from src.audio import music
from src.chat import Chat
from src.constants import IMAGE_TRIGGER_PHRASES

AUDIO_REQUIRED_VARS = ["LAVALINK_HOST", "LAVALINK_PORT", "LAVALINK_PASSWORD"]
# Chat also requires an API key, but the var name will be different
# depending on whatever service being used, so can't check for.
CHAT_REQUIRED_VARS = ["LLM_MODEL"]
MISC_REQUIRED_VARS = []
ROLLING_REQUIRED_VARS = []
SCHEDULING_REQUIRED_VARS = [
    "NOTION_BASE_URL",
    "NOTION_DATASOURCE_ID",
    "NOTION_API_KEY",
    "NOTION_VERSION",
]

bot = hikari.GatewayBot(
    intents=hikari.Intents.ALL,
    suppress_optimization_warning=True,
    banner=None,
    token=os.environ["DISCORD_API_KEY"],
)
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


async def handle_image_request(message: hikari.Message) -> bool:
    """
    Generates an image if the message asks for one, or edits the image if the
    message is a reply to one of the bot's images. Failures are only logged.

    :param message: The message the bot was mentioned in
    :type message: hikari.Message
    :return: True if the message was an image request, False otherwise
    :rtype: bool
    """
    prompt = re.sub(r"<@!?\d+>", "", message.content or "").strip()

    source_image = None
    ref = message.referenced_message
    if ref and ref.author and ref.author.id == BOT_USER_ID:
        attachment = next(
            (a for a in ref.attachments if (a.media_type or "").startswith("image/")),
            None,
        )
        if attachment:
            source_image = BinaryImage(
                data=await attachment.read(), media_type=attachment.media_type
            )

    if source_image is None and not any(
        phrase in prompt.lower() for phrase in IMAGE_TRIGGER_PHRASES
    ):
        return False

    logger.info(f"Generating image for: {prompt}")
    image = await chat_inst.generate_image(prompt, source_image)
    if image is not None:
        await message.respond(
            attachment=hikari.Bytes(image.data, f"image.{image.format}"),
            reply=message,
        )
    return True


async def handle_mention(message: hikari.Message) -> None:
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

    if chat_inst.image_agent is not None and await handle_image_request(message):
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


# ---------------------------------------------------------------------------
# Discord Events
# ---------------------------------------------------------------------------


BOT_USER_ID = None


@bot.listen()
async def on_ready(event: hikari.StartedEvent) -> None:
    """
    on_ready gets called when the bot starts up or potentially when restarts
    in event of a reconnection.
    """
    global BOT_USER_ID

    me = bot.get_me()
    if me is not None:
        BOT_USER_ID = me.id
    else:
        logger.warning("Could not determine bot user ID in on_ready.")
    logger.info("Dolores has connected to Discord.")


@bot.listen()
async def on_message(event: hikari.MessageCreateEvent) -> None:
    """
    on_message is the base function for handling any message that is sent on the server.
    There are a couple special cases that are handled here.
    """
    # Ignore various non-human messages
    if not event.is_human:
        return
    if event.message.content is None:
        return
    if "@everyone" in event.message.content:
        return

    me = bot.get_me()

    if me is None:
        logger.warning("Could not determine bot user ID in on_message.")
        return

    # Replies to the bot count as mentions, even with reply-ping turned off
    ref = event.message.referenced_message
    if me.id in event.message.user_mentions_ids or (
        ref and ref.author and ref.author.id == me.id
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
        client.register(music)
    if check_for_required_env_vars(MISC_REQUIRED_VARS):
        logger.info("Loading misc module")
        await client.load_extensions("misc")
    if check_for_required_env_vars(ROLLING_REQUIRED_VARS):
        logger.info("Loading rolling module")
        await client.load_extensions("rolling")
    if check_for_required_env_vars(SCHEDULING_REQUIRED_VARS):
        logger.info("Loading scheduling module")
        await client.load_extensions("scheduling")

    await client.start()


@bot.listen()
async def on_voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:
    """
    Handle voice state updates for lavalink integration.
    This is required for lavalink to know about voice connections.
    """
    from src.lavaclient import music_client

    if music_client and music_client.lavalink and event.state and BOT_USER_ID:
        lava_data = {
            "t": "VOICE_STATE_UPDATE",
            "d": {
                "guild_id": str(event.guild_id),
                "user_id": str(BOT_USER_ID),
                "session_id": event.state.session_id,
                "channel_id": str(event.state.channel_id)
                if event.state.channel_id
                else None,
            },
        }
        logger.debug(f"Voice state update data: {lava_data}")
        await music_client.lavalink.voice_update_handler(lava_data)


@bot.listen()
async def on_voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:
    """
    Handle voice server updates for lavalink integration.
    This is required for lavalink to connect to Discord's voice servers.
    """
    from src.lavaclient import music_client

    if event.endpoint is None:
        return

    if music_client and music_client.lavalink:
        lava_data = {
            "t": "VOICE_SERVER_UPDATE",
            "d": {
                "guild_id": str(event.guild_id),
                "token": event.token,
                # Remove "wss://" prefix
                "endpoint": event.endpoint[6:],
            },
        }
        logger.debug(f"Voice server update data: {lava_data}")
        await music_client.lavalink.voice_update_handler(lava_data)


if __name__ == "__main__":
    """
    Main program entry point
    """
    chat_inst = Chat() if check_for_required_env_vars(CHAT_REQUIRED_VARS) else None
    bot.run()
