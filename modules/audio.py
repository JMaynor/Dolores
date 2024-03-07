"""
audio.py module
"""

import asyncio
import queue

import discord
import yt_dlp
from discord.ext import bridge, commands

from configload import config

yt_dlp.utils.bug_reports_message = lambda: ""
ffmpeg_options = {"options": "-vn"}
ytdl = yt_dlp.YoutubeDL(config["YTDL"])


class AudioPlayer:
    def __init__(self) -> None:
        self.queue = queue.Queue()

    def add_to_queue(self, audio_file):
        self.queue.put(audio_file)

    def play(self):
        while not self.queue.empty():
            audio_file = self.queue.get()


class YTDLSource(discord.PCMVolumeTransformer):
    """
    The YTDLSource class represents an individual source of music.
    """

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        """
        from_url pulls in the actual audio data from a given URL
        """
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        if "entries" in data:
            # take all items from a playlist
            playlist = data["entries"]
            sources = []
            for entry in playlist:
                try:
                    source = cls(
                        discord.FFmpegPCMAudio(
                            ytdl.prepare_filename(entry), **ffmpeg_options
                        ),
                        data=entry,
                    )
                    sources.append(source)
                except Exception as e:
                    print(e)
            return sources
        else:
            try:
                filename = data["url"] if stream else ytdl.prepare_filename(data)
            except Exception as e:
                print(e)
                filename = None
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class audio(commands.Cog):
    """
    The audio class contains all commands related to playing audio.
    """

    def __init__(self, bot):
        self.bot = bot

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
