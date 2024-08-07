"""
Dolores is a chatbot that connects to a Discord server. Her primary use
is in being able to roll dice for players of a tabletop roleplaying game
but she is also capable of doing some basic audio things.
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Check if .env file present, if so load vars from it
if os.path.exists(".env"):
    load_dotenv()

from logger import logger
from modules import *

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(case_insensitive=True, intents=intents)

# Add main cog module, no 3rd party dependencies so no reason not to add
bot.add_cog(rolling(bot))

# Add modules based on config
# These rely on other dependencies and APIs so only add if enabled
if os.environ["AUDIO_ENABLED"].lower() == "true":
    bot.add_cog(audio(bot))
if os.environ["SCHEDULING_ENABLED"].lower() == "true":
    bot.add_cog(scheduling(bot))
if os.environ["TEXT_ENABLED"].lower() == "true":
    bot.add_cog(text(bot))

with open(os.path.join("locales", "strings.json"), "r") as f:
    summary_exclude_strings = json.load(f).get("SUMMARY_EXCLUDED_STRINGS", [])


async def handle_mention(message):
    """
    handle_mention is a coroutine that handles the bot's response to being mentioned
    in a message. It will generate a reply to the message and send it to the channel
    where the message was posted.
    """
    ctx = await bot.get_context(message)

    if os.environ["TEXT_ENABLED"].lower() == "true":
        text_instance = text(bot)
        clean_message = message.clean_content.replace("@Dolores", "Dolores")
        clean_message = clean_message.replace("@everyone", "everyone")
        clean_message = clean_message.replace("@Testie", "Testie")
        await ctx.defer()
        reply = text_instance.generate_reply(clean_message)
    else:
        reply = "Hi"
    if reply != "":
        await ctx.respond(reply)


async def handle_news(message):
    """
    handle_news handles bot's response when a news article is posted in the news channel
    """
    ctx = await bot.get_context(message)
    # Try and extract URL from message
    url = re.search(r"(https?://[^\s]+)", message.clean_content)
    if url is not None:
        text_instance = text(bot)
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
                        await ctx.respond(embed=embed)


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
    await ctx.defer()
    if os.environ["TEXT_ENABLED"].lower() == "true":
        text_instance = text(bot)
        if isinstance(error, (commands.CommandNotFound)):
            await ctx.send(text_instance.generate_snarky_comment())
        else:
            logger.error(error)
    else:
        await ctx.send("An error occurred. Please try again.")


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
        await handle_mention(message)

    # Check for if message was posted in news channel and contains a non-media URL
    # if (
    #     os.environ["TEXT_ENABLED"].lower() == "true"
    #     and message.channel.id == int(os.environ["NEWS_CHANNEL_ID"])
    #     and "https" in message.clean_content
    #     and not any(
    #         excluded in message.clean_content for excluded in summary_exclude_strings
    #     )
    # ):
    #     await handle_news(message)

    # Normal command processing
    await bot.process_commands(message)


if __name__ == "__main__":
    """
    Main program entry point
    """
    bot.run(os.environ["DISCORD_API_KEY"])
