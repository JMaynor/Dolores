"""
Module contains code that deals with playing audio in voice channels.
Much has come directly from the pomice example bot so most of module relies on
having a lavalink server running.
"""

import asyncio
import math
import os
from contextlib import suppress
from typing import Optional

import discord
import pomice
from discord.ext import commands

from src.modules.logger import logger


class Player(pomice.Player):
    """
    Custom pomice Player class.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.queue = pomice.Queue()
        self.controller: discord.Message = None
        # Set context here so we can send a now playing embed
        self.context: commands.Context = None
        self.dj: discord.Member = None

        self.pause_votes = set()
        self.resume_votes = set()
        self.skip_votes = set()
        self.shuffle_votes = set()
        self.stop_votes = set()

    async def do_next(self) -> None:
        # Clear the votes for a new song
        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        # Check if theres a controller still active and deletes it
        if self.controller:
            with suppress(discord.HTTPException):
                await self.controller.delete()

        # Queue up the next track, else teardown the player
        try:
            track: pomice.Track = self.queue.get()
        except pomice.QueueEmpty:
            return await self.teardown()

        await self.play(track)

        # Call the controller (a.k.a: The "Now Playing" embed) and check if one exists

        if track.is_stream:
            embed = discord.Embed(
                title="Now playing",
                description=f":red_circle: **LIVE** [{track.title}]({track.uri})",
            )
            self.controller = await self.context.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"Now playing",
                description=f"[{track.title}]({track.uri})",
            )
            self.controller = await self.context.send(embed=embed)

    async def teardown(self):
        """
        Clear internal states, remove player controller and disconnect.
        """
        with suppress((discord.HTTPException), (KeyError)):
            await self.destroy()
            if self.controller:
                await self.controller.delete()

    async def set_context(self, ctx: commands.Context):
        """
        Set context for the player
        """
        self.context = ctx
        self.dj = ctx.author


class audio(commands.Cog):
    """
    The audio class contains all commands related to playing audio.
    """

    def __init__(self, bot):
        self.bot = bot
        self.pomice = pomice.NodePool()
        self.queue = pomice.Queue()
        bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        # Waiting for the bot to get ready before connecting to nodes.
        await self.bot.wait_until_ready()

        await self.pomice.create_node(
            bot=self.bot,
            host=os.environ["LAVALINK_HOST"],
            port=int(os.environ["LAVALINK_PORT"]),
            password=os.environ["LAVALINK_PASSWORD"],
            identifier="Dolores",
        )

    def required(self, ctx: commands.Context):
        """
        Method which returns required votes based on amount of members in a channel.
        """
        player: Player = ctx.voice_client
        channel = self.bot.get_channel(int(player.channel.id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        assert ctx.command is not None
        if ctx.command.name == "stop":
            if len(channel.members) == 3:
                required = 2

        return required

    def is_privileged(self, ctx: commands.Context):
        """
        Check whether the user is an Admin or DJ.
        """
        assert ctx.voice_client is not None
        player: Player = ctx.voice_client

        return player.dj == ctx.author or ctx.author.guild_permissions.kick_members

    # Pomice event listeners
    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: Player, track, _):
        await player.do_next()

    @commands.Cog.listener()
    async def on_pomice_track_stuck(self, player: Player, track, _):
        logger.error(f"Track stuck: {track.title}")
        await player.do_next()

    @commands.Cog.listener()
    async def on_pomice_track_exception(self, player: Player, track, _):
        logger.error(f"Track exception: {track.title}")
        await player.do_next()

    @commands.slash_command(
        description="Joins voice channel of user who called the command."
    )
    async def join(
        self,
        ctx: discord.commands.context.ApplicationContext,
        *,
        channel: discord.VoiceChannel = None,
    ) -> None:
        """
        Joins the voice channel of the user who called the command.
        Ex: /join
        """
        if not channel:
            channel = getattr(ctx.author.voice, "channel", None)
            if not channel:
                raise commands.CheckFailure(
                    "You must be in a voice channel to use this command "
                    "without specifying the channel argument.",
                )
        assert ctx.author is None
        await ctx.author.voice.channel.connect(cls=Player)
        player: Player = ctx.voice_client

        # Set the player context so we can use it so send messages
        await player.set_context(ctx=ctx)
        await ctx.send(f"Joined the voice channel `{channel}`")

    @commands.slash_command(description="Disconnects Dolores from voice channel.")
    async def leave(self, ctx: discord.commands.context.ApplicationContext):
        """
        Disconnects Dolores from voice chat channel, if she is connected.
        Also stops any currently playing music
        Ex: /leave
        """
        if not (player := ctx.voice_client):
            return await ctx.send(
                "You must have the bot in a channel in order to use this command",
                delete_after=7,
            )

        await player.destroy()
        await ctx.send("Dolores has left the building.")

    @commands.slash_command(description="Play audio stream in user's voice channel.")
    async def play(
        self, ctx: discord.commands.context.ApplicationContext, *, search: str
    ) -> None:
        """
        Plays audio from a given search term.
        Ex: /play https://www.youtube.com/watch?v=O1OTWCd40bc
        Dolores will play Wicked Games by The Weeknd
        """
        # Checks if the player is in the channel before we play anything
        if not (player := ctx.voice_client):
            await ctx.author.voice.channel.connect(cls=Player)
            player: Player = ctx.voice_client
            await player.set_context(ctx=ctx)

        # If you search a keyword, Pomice will automagically search the result using YouTube
        # You can pass in "search_type=" as an argument to change the search type
        # i.e: player.get_tracks("query", search_type=SearchType.ytmsearch)
        # will search up any keyword results on YouTube Music

        # We will also set the context here to get special features, like a track.requester object
        results = await player.get_tracks(search, ctx=ctx)

        if not results:
            await ctx.send("No results were found for that search term", delete_after=7)

        assert results is not None

        if isinstance(results, pomice.Playlist):
            for track in results.tracks:
                player.queue.put(track)
        else:
            track = results[0]
            player.queue.put(track)

        if not player.is_playing:
            await player.do_next()

    @commands.slash_command(description="Pauses the currently playing audio.")
    async def pause(self, ctx: discord.commands.context.ApplicationContext):
        """
        Pauses the currently playing audio
        Ex: /pause
        """
        if not (player := ctx.voice_client):
            return await ctx.send(
                "You must have the bot in a channel in order to use this command",
                delete_after=7,
            )

        if player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send("An admin or DJ has paused the player.", delete_after=10)
            player.pause_votes.clear()

            return await player.set_pause(True)

        required = self.required(ctx)
        player.pause_votes.add(ctx.author)

        if len(player.pause_votes) >= required:
            await ctx.send("Vote to pause passed. Pausing player.", delete_after=10)
            player.pause_votes.clear()
            await player.set_pause(True)
        else:
            await ctx.send(
                f"{ctx.author.mention} has voted to pause the player. Votes: {len(player.pause_votes)}/{required}",
                delete_after=15,
            )

    @commands.slash_command(description="Resumes the currently paused audio.")
    async def resume(self, ctx: discord.commands.context.ApplicationContext):
        """
        Resumes the currently paused audio
        Ex: /resume
        """
        if not (player := ctx.voice_client):
            return await ctx.send(
                "You must have the bot in a channel in order to use this command",
                delete_after=7,
            )

        if not player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send("An admin or DJ has resumed the player.", delete_after=10)
            player.resume_votes.clear()

            return await player.set_pause(False)

        required = self.required(ctx)
        player.resume_votes.add(ctx.author)

        if len(player.resume_votes) >= required:
            await ctx.send("Vote to resume passed. Resuming player.", delete_after=10)
            player.resume_votes.clear()
            await player.set_pause(False)
        else:
            await ctx.send(
                f"{ctx.author.mention} has voted to resume the player. Votes: {len(player.resume_votes)}/{required}",
                delete_after=15,
            )

    @commands.slash_command(description="Skips the currently playing song.")
    async def skip(self, ctx: discord.commands.context.ApplicationContext):
        """
        Skip the currently playing song.
        Ex: /skip
        """
        if not (player := ctx.voice_client):
            return await ctx.send(
                "You must have the bot in a channel in order to use this command",
                delete_after=7,
            )

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send("An admin or DJ has skipped the song.", delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            await ctx.send("The song requester has skipped the song.", delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.send("Vote to skip passed. Skipping song.", delete_after=10)
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.send(
                f"{ctx.author.mention} has voted to skip the song. Votes: {len(player.skip_votes)}/{required} ",
                delete_after=15,
            )

    @commands.slash_command(description="Shuffles the queue.")
    async def shuffle(self, ctx: discord.commands.context.ApplicationContext):
        """
        Shuffles the queue.
        Ex: /shuffle
        """
        if not (player := ctx.voice_client):
            return await ctx.send(
                "You must have the bot in a channel in order to use this command",
                delete_after=7,
            )
        if not player.is_connected:
            return

        if player.queue.qsize() < 3:
            return await ctx.send(
                "The queue is empty. Add some songs to shuffle the queue.",
                delete_after=15,
            )

        if self.is_privileged(ctx):
            await ctx.send("An admin or DJ has shuffled the queue.", delete_after=10)
            player.shuffle_votes.clear()
            return player.queue.shuffle()

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            await ctx.send(
                "Vote to shuffle passed. Shuffling the queue.", delete_after=10
            )
            player.shuffle_votes.clear()
            player.queue.shuffle()
        else:
            await ctx.send(
                f"{ctx.author.mention} has voted to shuffle the queue. Votes: {len(player.shuffle_votes)}/{required}",
                delete_after=15,
            )

    @commands.slash_command(description="Stops the currently playing audio.")
    async def stop(self, ctx: discord.commands.context.ApplicationContext):
        """
        Stops the currently playing song, if one is playing.
        Ex: /stop
        """
        assert ctx.voice_client is not None
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.respond("Stopped playing.")
