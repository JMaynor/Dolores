"""
audio.py module
"""

import asyncio

import discord
import pomice
from discord.ext import bridge, commands

from configload import config


class audio(commands.Cog):
    """
    The audio class contains all commands related to playing audio.
    """

    def __init__(self, bot):
        self.bot = bot
        self.pomice = pomice.NodePool()
        self.queue = pomice.Queue()

    async def start_nodes(self):
        await self.pomice.create_node(
            bot=self.bot,
            host=config["LAVALINK"]["host"],
            port=config["LAVALINK"]["port"],
            password=config["LAVALINK"]["password"],
            identifier="Dolores",
        )

    @bridge.bridge_command(
        description="Use's yt-dlp to play an audio stream in the user's voice channel."
    )
    async def play(self, ctx, *, url):
        """
        Plays a song from a given URL in the user's current voice channel.
        Valid URLS are Youtube and Soundcloud
        Ex: -play https://www.youtube.com/watch?v=O1OTWCd40bc
        Dolores will play Wicked Games by The Weeknd
        """
        await ctx.defer()
        member = ctx.guild.get_member(ctx.author.id)
        try:
            channel = member.voice.channel
            if channel and ctx.voice_client is None:
                voice = await channel.connect()
        except AttributeError:
            await ctx.respond("Must be connected to voice channel to play audio.")

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=False)
        voice.play(
            player, after=lambda e: print("Player error: {}".format(e)) if e else None
        )
        await ctx.respond("Now playing: {}".format(player.title))
        while True:
            await asyncio.sleep(5)
            if not ctx.voice_client.is_playing():
                await ctx.voice_client.disconnect()
                break

    @bridge.bridge_command(description="Stops the currently playing audio.")
    async def stop(self, ctx):
        """
        Stops the currently playing song, if one is playing.
        Ex: -stop
        """
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.respond("Stopped playing.")

    @bridge.bridge_command(description="Disconnects Dolores from voice channel.")
    async def leave(self, ctx):
        """
        Disconnects Dolores from voice chat channel, if she is connected.
        Also stops any currently playing music
        Ex: -leave
        """
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.respond("Disconnected from voice channel.")
