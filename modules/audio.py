"""
audio.py module

Much has come from the pomice example bot
"""

import asyncio
from contextlib import suppress

import discord
import pomice
from discord.ext import bridge, commands

from configload import config


class Player(pomice.Player):
    """Custom pomice Player class."""

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
                description=f":red_circle: **LIVE** [{track.title}]({track.uri}) [{track.requester.mention}]",
            )
            self.controller = await self.context.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"Now playing",
                description=f"[{track.title}]({track.uri}) [{track.requester.mention}]",
            )
            self.controller = await self.context.send(embed=embed)

    async def teardown(self):
        """Clear internal states, remove player controller and disconnect."""
        with suppress((discord.HTTPException), (KeyError)):
            await self.destroy()
            if self.controller:
                await self.controller.delete()

    async def set_context(self, ctx: commands.Context):
        """Set context for the player"""
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

    async def start_nodes(self):
        await self.pomice.create_node(
            bot=self.bot,
            host=config["LAVALINK"]["host"],
            port=config["LAVALINK"]["port"],
            password=config["LAVALINK"]["password"],
            identifier="Dolores",
        )

    @bridge.bridge_command(
        description="Joins the voice channel of the user who called the command."
    )
    async def join(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel = None
    ) -> None:
        """
        Joins the voice channel of the user who called the command.
        """
        if not channel:
            channel = getattr(ctx.author.voice, "channel", None)
            if not channel:
                raise commands.CheckFailure(
                    "You must be in a voice channel to use this command "
                    "without specifying the channel argument.",
                )
        await ctx.author.voice.channel.connect(cls=pomice.Player)

        player: Player = ctx.voice_client

        # Set the player context so we can use it so send messages
        await player.set_context(ctx=ctx)
        await ctx.send(f"Joined the voice channel `{channel}`")

    @bridge.bridge_command(description="Disconnects Dolores from voice channel.")
    async def leave(self, ctx: commands.Context) -> None:
        """
        Disconnects Dolores from voice chat channel, if she is connected.
        Also stops any currently playing music
        Ex: -leave
        """
        if not ctx.voice_client:
            raise commands.CommandError("No player detected")

        player: pomice.Player = ctx.voice_client

        await player.destroy()
        await ctx.send("Dolores has left the building.")

    @bridge.bridge_command(
        description="Use's pomice/lavalink to play an audio stream in the user's voice channel."
    )
    async def play(self, ctx: commands.Context, *, search: str) -> None:
        """
        Plays a song from a given URL in the user's current voice channel.
        Valid URLS are Youtube and Soundcloud
        Ex: -play https://www.youtube.com/watch?v=O1OTWCd40bc
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

        if isinstance(results, pomice.Playlist):
            for track in results.tracks:
                player.queue.put(track)
        else:
            track = results[0]
            player.queue.put(track)

        if not player.is_playing:
            await player.do_next()

    @bridge.bridge_command(aliases=["n", "nex", "next", "sk"])
    async def skip(self, ctx: commands.Context):
        """
        Skip the currently playing song.
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

    @bridge.bridge_command(description="Stops the currently playing audio.")
    async def stop(self, ctx):
        """
        Stops the currently playing song, if one is playing.
        Ex: -stop
        """
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.respond("Stopped playing.")
