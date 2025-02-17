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

from modules import audio, generation, rolling, scheduling
from modules.logger import logger

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(case_insensitive=True, intents=intents)

# Add main cog module, no 3rd party dependencies so no reason not to add
bot.add_cog(rolling(bot))

# Add modules based on config
# These rely on other dependencies and APIs so only add if enabled
if os.environ.get("AUDIO_ENABLED", "false").lower() == "true":
    bot.add_cog(audio(bot))
if os.environ.get("SCHEDULING_ENABLED", "false").lower() == "true":
    bot.add_cog(scheduling(bot))
if os.environ.get("GENERATION_ENABLED", "false").lower() == "true":
    bot.add_cog(generation(bot))


async def handle_mention(message):
    """
    handle_mention is a coroutine that handles the bot's response to being mentioned
    in a message. It will generate a reply to the message and send it to the channel
    where the message was posted.
    """
    ctx = await bot.get_context(message)

    if os.environ.get("GENERATION_ENABLED", "false").lower() == "true":
        text_instance = generation(bot)
        clean_message = message.clean_content.replace("@Dolores", "Dolores")
        clean_message = clean_message.replace("@everyone", "everyone")
        clean_message = clean_message.replace("@Testie", "Testie")
        logger.info(f"Generating reply to following message: {clean_message}")
        reply = text_instance.generate_reply(message.author.global_name, clean_message)
    else:
        reply = "Hi"
    if reply != "":
        await ctx.reply(reply)


async def handle_news(message):
    """
    handle_news handles bot's response when a news article is posted in the news channel
    """
    ctx = await bot.get_context(message)
    # Try and extract URL from message
    url = re.search(r"(https?://[^\s]+)", message.clean_content)
    if url is not None:
        text_instance = generation(bot)
        # If URL is found, get a summary of the article
        summary = text_instance.summarize_url(url.group(0).split("?")[0])

        # If the summary is too short, don't post it
        if summary != "":
            if "sm_api_content_reduced" in summary:
                reduced_amount = summary["sm_api_content_reduced"].replace("%", "")
                if int(reduced_amount) > int(
                    os.environ.get("SMMRY_MIN_REDUCED_AMOUNT", 65)
                ):
                    if "sm_api_title" in summary:
                        embed_title = summary["sm_api_title"]
                    else:
                        embed_title = "Summary"
                    embed = discord.Embed(title=embed_title)
                    embed.add_field(
                        name="Article Summary", value=summary["sm_api_content"]
                    )
                    if len(summary["sm_api_content"]) <= 1024:
                        await ctx.reply(embed=embed)


async def handle_question(message):
    """
    When someone reacts with a question mark to a message, Dolores will attempt
    to explain the contents of the message in an informative simpler way.
    Calls generate_explanation in the generation module.
    """
    ctx = await bot.get_context(message)

    text_instance = generation(bot)
    logger.info(f"Generating explanation for message: {message.clean_content}")
    explanation = text_instance.generate_explanation(
        message.author.global_name, message.clean_content
    )
    if explanation != "":
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
    text_instance = generation(bot)
    if isinstance(error, (commands.CommandNotFound)):
        await ctx.send(text_instance.generate_snarky_comment())
    else:
        await ctx.send("An error occurred. Please try again.")


@bot.event
async def on_reaction_add(reaction, user):
    """
    on_reaction_add is a base function for handling when a reaction is added
    to a message. Currently used to check for question mark reaction
    """
    if os.environ.get("GENERATION_ENABLED", "false").lower() == "true":
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
