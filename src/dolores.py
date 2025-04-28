"""
Dolores is a chatbot that connects to a Discord server. Her primary use
is in being able to roll dice for players of a tabletop roleplaying game
but she is also capable of doing some basic audio things.
"""

import os
import re

import hikari
import hikari.events.reaction_events
import lightbulb
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))

# Check if .env file present, if so load vars from it
if os.path.exists(os.path.join(current_dir, "..", ".env")):
    load_dotenv()

from src._logger import logger
from src.modules.chat import chat

bot = hikari.GatewayBot(intents=hikari.Intents.ALL, token=os.environ["DISCORD_API_KEY"])
client = lightbulb.client_from_app(bot)
chat_inst = chat()


async def handle_mention(message: hikari.Message):
    """
    handle_mention is a coroutine that handles the bot's response to being mentioned
    in a message. It will generate a reply to the message and send it to the channel
    where the message was posted.
    TODO: Add a check to see if chat module is loaded before trying to use it.
    """
    message_content = message.content
    if message_content is None:
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
    TODO: Add a check to see if chat module is loaded before trying to use it.
    """
    message_content = message.content
    if message_content is None:
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
    # TODO Add check for if chat module has been loaded once hikari version of that is added
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
    await client.load_extensions(
        "modules.images", "modules.rolling", "modules.scheduling"
    )
    await client.start()


if __name__ == "__main__":
    """
    Main program entry point
    """
    bot.run()
