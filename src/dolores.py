"""
Dolores is a chatbot that connects to a Discord server. Her primary use
is in being able to roll dice for players of a tabletop roleplaying game
but she is also capable of doing some basic audio things.
"""

import os
import re

import discord
from discord.ext import commands
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))

# Check if .env file present, if so load vars from it
if os.path.exists(os.path.join(current_dir, "..", ".env")):
    load_dotenv()

from modules import audio, chat, images, rolling, scheduling
from modules._logger import logger

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(case_insensitive=True, intents=intents)


def check_required_vars(var_list):
    """
    Checks if all environment variables in the list are set and non-empty.
    """
    missing_vars = [var for var in var_list if not os.environ.get(var)]
    if missing_vars:
        logger.warning(
            f"Required environment variables missing: {', '.join(missing_vars)}"
        )
        return False
    return True


# Define the minimum required environment variables for each module to function.
AUDIO_REQUIRED_VARS = ["LAVALINK_HOST", "LAVALINK_PORT", "LAVALINK_PASSWORD"]
CHAT_REQUIRED_VARS = []
IMAGES_REQUIRED_VARS = ["OPENAI_API_KEY", "IMAGE_MODEL"]
ROLLING_REQUIRED_VARS = []  # No req vars for rolling, uses built-in python libs
SCHEDULING_REQUIRED_VARS = [
    "NOTION_BASE_URL",
    "NOTION_DATABASE_ID",
    "NOTION_API_KEY",
    "NOTION_VERSION",
]

# Attempt to load modules based on required environment variables
modules_to_load = [
    (audio, AUDIO_REQUIRED_VARS, "Audio"),
    (chat, CHAT_REQUIRED_VARS, "Chat"),
    (images, IMAGES_REQUIRED_VARS, "Images"),
    (rolling, ROLLING_REQUIRED_VARS, "Rolling"),
    (scheduling, SCHEDULING_REQUIRED_VARS, "Scheduling"),
]

for cog_class, required_vars, module_name in modules_to_load:
    if check_required_vars(required_vars):
        try:
            bot.add_cog(cog_class(bot))
            logger.info(f"{module_name} module loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load {module_name} module: {e}")
    else:
        logger.warning(
            f"{module_name} module not loaded due to missing environment variables."
        )


async def handle_mention(message):
    """
    handle_mention is a coroutine that handles the bot's response to being mentioned
    in a message. It will generate a reply to the message and send it to the channel
    where the message was posted.
    """
    ctx = await bot.get_context(message)

    # Check if the chat cog is loaded before trying to use it
    chat_cog = bot.get_cog("chat")
    if chat_cog:
        clean_message = message.clean_content.replace("@Dolores", "Dolores")
        clean_message = clean_message.replace("@everyone", "everyone")
        clean_message = clean_message.replace("@Testie", "Testie")

        # Remove invalid characters from author name for openai
        author = message.author.global_name or message.author.name  # Fallback to name
        author = re.sub(r"[^a-zA-Z0-9_]", "", author)
        author = author.replace(" ", "_")
        author = author.lower() or "discord_user"  # Ensure not empty

        logger.info(f"Generating reply to following message: {clean_message}")
        reply = await getattr(chat_cog, "generate_reply")(author, clean_message)
    else:
        reply = "Hi"

    if reply != "":
        await ctx.reply(reply)


async def handle_question(message):
    """
    When someone reacts with a question mark to a message, Dolores will attempt
    to explain the contents of the message in an informative simpler way.
    Calls generate_explanation in the generation module.
    """
    ctx = await bot.get_context(message)

    # Check if the chat cog is loaded before trying to use it
    chat_cog = bot.get_cog("chat")
    if chat_cog:
        # Remove invalid characters from author name for openai
        author = message.author.global_name or message.author.name  # Fallback to name
        author = re.sub(r"[^a-zA-Z0-9_]", "", author)
        author = author.replace(" ", "_")
        author = author.lower() or "discord_user"

        logger.info(f"Generating explanation for message: {message.clean_content}")
        generate_explanation = getattr(chat_cog, "generate_explanation", None)
        if generate_explanation:
            explanation = await generate_explanation(author, message.clean_content)
            if explanation:
                await ctx.reply(explanation)


# ---------------------------------------------------------------------------
# Discord Events
# ---------------------------------------------------------------------------


@bot.event
async def on_ready():
    """
    on_ready gets called when the bot starts up or potentially when restarts
    in event of a reconnection.
    """
    assert bot.user is not None
    logger.info("Dolores has connected to Discord.")


@bot.event
async def on_command_error(ctx, error):
    """
    on_command_error overrides default py-cord command error behavior. If someone
    tries to use a command that does not exist, Dolores will reply with a snarky
    comeback. Any other error performs default behavior of logging to syserr.
    """
    logger.error(error)
    chat_cog = bot.get_cog("chat")
    if chat_cog and isinstance(error, commands.CommandNotFound):
        generate_snark = getattr(chat_cog, "generate_snarky_comment", None)
        if generate_snark:
            snarky_comment = generate_snark()
            await ctx.send(snarky_comment)
    else:
        await ctx.send("An error occurred. Please try again.")


@bot.event
async def on_reaction_add(reaction, user):
    """
    on_reaction_add is a base function for handling when a reaction is added
    to a message. Currently used to check for question mark reaction
    """
    if os.environ.get("CHAT_ENABLED", "false").lower() == "true":
        if user == bot.user:
            return
        if reaction.emoji == "❓" or reaction.emoji == "❔":
            await handle_question(reaction.message)


@bot.event
async def on_message(message):
    """
    on_message is the base function for handling any message that is sent on the server.
    There are a couple special cases that are handled here, otherwise passes
    the message to the normal command processor.
    """

    # If someone mentions Dolores, she will respond to them,
    # unless she is the one who sent the message or it is an @everyone mention
    assert bot.user is not None
    if (
        bot.user.mentioned_in(message)
        and message.author.id != bot.user.id
        and "@everyone" not in message.clean_content
    ):
        # For testing, print out attributes of message
        logger.info(f"Message: {message}")
        await handle_mention(message)
        return

    # Normal command processing
    await bot.process_commands(message)


if __name__ == "__main__":
    """
    Main program entry point
    """
    bot.run(os.environ["DISCORD_API_KEY"])
