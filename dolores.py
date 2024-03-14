"""
dolores.py
Author: Jordan Maynor
Date: Apr 2020

Dolores is a chatbot that connects to a Discord server. Her primary use
is in being able to roll dice for players of a tabletop roleplaying game
but she is also capable of doing some basic audio things.

Majority of functionality has been organized into separate modules.
dolores.py - Main program file. Handles Discord-related functionality and events
audio.py - Handles all audio/yt-dlp related functionality
rolling.py - Handles all dice-rolling/randomization functionality
scheduling.py - Handles all Notion/Twitch scheduling functionality
text.py - Handles all text-related functionality
"""

import asyncio
import re
import sys
from datetime import datetime

import discord
from discord.ext import bridge, commands

from configload import config
from modules import *
from notify import notif

intents = discord.Intents.all()
intents.members = True
bot = bridge.Bot(command_prefix="-", case_insensitive=True, intents=intents)

# Add all Cog modules
bot.add_cog(rolling(bot))
bot.add_cog(audio(bot))
bot.add_cog(scheduling(bot))
bot.add_cog(text(bot))


async def handle_mention(message):
    """
    handle_mention is a coroutine that handles the bot's response to being mentioned
    in a message. It will generate a reply to the message and send it to the channel
    where the message was posted.
    """
    ctx = await bot.get_context(message)
    text_instance = text(bot)
    clean_message = message.clean_content.replace("@Dolores", "Dolores")
    clean_message = clean_message.replace("@everyone", "everyone")
    clean_message = clean_message.replace("@Testie", "Testie")
    await ctx.defer()
    reply = text_instance.generate_reply(clean_message)
    if reply != "":
        await ctx.respond(reply)


async def handle_news(message):
    """
    handle_news handles bot's response when a news article is posted in the news channel
    TODO: Currently not being called. Consider using some other service.
    Too frequently summary isn't useful. Not necessarily SMMRY's fault.
    It's because too much bullshit is on modern "news" sites that it's not able
    to pull the actual article content. But maybe some other approach would be
    better. Look into web scrapers. Firefox's reader mode comes to mind.
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
                if int(reduced_amount) > config["SMMRY"]["min_reduced_amount"]:
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
    in event of reconnection. It prints some basic info to the console.
    """
    print("Time is: ", datetime.now())
    print("Bring yourself online, ", bot.user.name)
    print("-----------------------------")


@bot.event
async def on_command_error(ctx, error):
    """
    on_command_error overrides default py-cord command error behavior. If someone
    tries to use a command that does not exist, Dolores will reply with a snarky
    comeback. Any other error performs default behavior of logging to syserr.
    """
    await ctx.defer()
    text_instance = text(bot)
    if isinstance(error, (commands.CommandNotFound)):
        await ctx.send(text_instance.generate_snarky_comment())
    else:
        notif.notify(f"Error: {error}")
        print(error, file=sys.stderr)


@bot.event
async def on_message(message):
    """
    on_message is the base function for handling any message that is sent on the server.
    There are a couple special cases that are handled here, otherwise passes
    the message to the normal command processor.
    """

    # If someone mentions Dolores, she will respond to them,
    # unless she is the one who sent the message
    if (bot.user.mentioned_in(message)) and (message.author.id != bot.user.id):
        await handle_mention(message)

    # Check for if message was posted in news channel and contains a non-media URL
    if (
        message.channel.id == config["DISCORD"]["news_channel_id"]
        and "https" in message.clean_content
        and not any(
            excluded in message.clean_content
            for excluded in config["SMMRY"]["excluded_strings"]
        )
    ):
        # await handle_news(message)
        pass

    # Normal command processing
    await bot.process_commands(message)


if __name__ == "__main__":
    """
    Main program entry point
    """
    print("Starting main program...")
    bot.run(config["DISCORD"]["bot_api_key"])
