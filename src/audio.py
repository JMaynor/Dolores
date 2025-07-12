"""
Module contains code that deals with playing audio in voice channels.
"""

import logging
from typing import cast

import hikari
import lightbulb

from src.lavaclient import get_music_client

logger = logging.getLogger(__name__)
music = lightbulb.Group("music", "music commands")


def get_app_from_context(ctx: lightbulb.Context) -> hikari.GatewayBot:
    """
    Helper function to get the bot app from context.
    """
    return cast(hikari.GatewayBot, ctx.client.app)


def safe_guild_id(ctx: lightbulb.Context) -> int:
    """
    Helper function to safely get guild ID as int.
    """
    if ctx.guild_id is None:
        raise ValueError("Command must be used in a guild")
    return int(ctx.guild_id)


async def get_voice_channel(ctx: lightbulb.Context) -> int:
    """
    Helper function to get user's voice channel.
    """
    app = get_app_from_context(ctx)
    guild_id = safe_guild_id(ctx)

    voice_state = app.cache.get_voice_state(guild_id, ctx.user.id)
    if not voice_state or not voice_state.channel_id:
        raise ValueError("You need to be in a voice channel to use this command!")

    return int(voice_state.channel_id)


@music.register
class Play(
    lightbulb.SlashCommand,
    name="play",
    description="Play a song or add it to the queue.",
):
    """
    Play a song from YouTube or add it to the queue if something is already playing.
    """

    query = lightbulb.string(
        "query", "The song or playlist to play. Can be a URL or search term."
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Play a track or add it to queue.
        """
        try:
            # Check if user is in a voice channel and get info
            voice_channel = await get_voice_channel(ctx)
            guild_id = safe_guild_id(ctx)
            app = get_app_from_context(ctx)

            # Get music client
            music_client = await get_music_client(app)
            if not music_client:
                await ctx.respond(
                    "❌ Music client is not available. Please check the lavalink configuration."
                )
                return

            # Initialize if needed
            if not music_client.is_initialized:
                if not await music_client.initialize():
                    await ctx.respond("❌ Failed to initialize music client.")
                    return

            # Connect to voice channel if not already connected
            if not await music_client.is_playing(guild_id):
                if not await music_client.connect_to_voice(guild_id, voice_channel):
                    await ctx.respond("❌ Failed to connect to voice channel.")
                    return

            await ctx.respond("🔍 Searching for tracks...")  # Search for tracks
            tracks = await music_client.search_tracks(self.query)
            if not tracks:
                # Check if there's nothing playing and no queue
                if not await music_client.is_playing(
                    guild_id
                ) and not music_client.get_queue(guild_id):
                    # Disconnect from voice channel since there's nothing to do
                    await music_client.disconnect_from_voice(guild_id)
                    await ctx.respond(
                        f"❌ No tracks found for query: `{self.query}`\n"
                        "🚪 Disconnected from voice channel since there's nothing to play."
                    )
                else:
                    await ctx.respond(f"❌ No tracks found for query: `{self.query}`")
                return

            # Play the first track
            track = tracks[0]
            requester_id = ctx.user.id
            requester_name = ctx.user.display_name or ctx.user.username

            success = await music_client.play_track(
                guild_id, track, requester_id, requester_name
            )

            if success:
                # Format duration
                duration_minutes = track.duration // 60000
                duration_seconds = (track.duration % 60000) // 1000
                duration_str = f"{duration_minutes}:{duration_seconds:02d}"

                if await music_client.is_playing(guild_id):
                    await ctx.respond(
                        f"🎵 **Added to queue:** {track.title} by {track.author} [{duration_str}]\n"
                        f"👤 Requested by {requester_name}"
                    )
                else:
                    await ctx.respond(
                        f"🎵 **Now playing:** {track.title} by {track.author} [{duration_str}]\n"
                        f"👤 Requested by {requester_name}"
                    )
            else:
                await ctx.respond("❌ Failed to play the track.")

        except ValueError as e:
            await ctx.respond(f"❌ {str(e)}")
        except Exception as e:
            logger.error(f"Error in play command: {e}")
            await ctx.respond("❌ An unexpected error occurred.")


@music.register
class Pause(
    lightbulb.SlashCommand,
    name="pause",
    description="Pause the currently playing track.",
):
    """
    Pause the currently playing track.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Pause playback.
        """
        try:
            guild_id = safe_guild_id(ctx)
            app = get_app_from_context(ctx)
            music_client = await get_music_client(app)

            if not music_client or not music_client.is_initialized:
                await ctx.respond("❌ Music client is not available.")
                return

            if not await music_client.is_playing(guild_id):
                await ctx.respond("❌ Nothing is currently playing.")
                return

            if await music_client.is_paused(guild_id):
                await ctx.respond("⏸️ Playback is already paused.")
                return

            success = await music_client.pause(guild_id)
            if success:
                await ctx.respond("⏸️ Playback paused.")
            else:
                await ctx.respond("❌ Failed to pause playback.")

        except Exception as e:
            logger.error(f"Error in pause command: {e}")
            await ctx.respond("❌ An unexpected error occurred.")


@music.register
class Resume(
    lightbulb.SlashCommand,
    name="resume",
    description="Resume the paused track.",
):
    """
    Resume the paused track.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Resume playback.
        """
        try:
            guild_id = safe_guild_id(ctx)
            app = get_app_from_context(ctx)
            music_client = await get_music_client(app)

            if not music_client or not music_client.is_initialized:
                await ctx.respond("❌ Music client is not available.")
                return

            if not await music_client.is_paused(guild_id):
                await ctx.respond("▶️ Playback is not paused.")
                return

            success = await music_client.resume(guild_id)
            if success:
                await ctx.respond("▶️ Playback resumed.")
            else:
                await ctx.respond("❌ Failed to resume playback.")

        except Exception as e:
            logger.error(f"Error in resume command: {e}")
            await ctx.respond("❌ An unexpected error occurred.")


@music.register
class Stop(
    lightbulb.SlashCommand,
    name="stop",
    description="Stop playback and clear the queue.",
):
    """
    Stop playback and clear the queue.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Stop playback and clear queue.
        """
        try:
            guild_id = safe_guild_id(ctx)
            app = get_app_from_context(ctx)
            music_client = await get_music_client(app)

            if not music_client or not music_client.is_initialized:
                await ctx.respond("❌ Music client is not available.")
                return

            if not await music_client.is_playing(
                guild_id
            ) and not await music_client.is_paused(guild_id):
                await ctx.respond("❌ Nothing is currently playing.")
                return

            success = await music_client.stop(guild_id)
            if success:
                # After stopping and clearing queue, disconnect from voice channel
                await music_client.disconnect_from_voice(guild_id)
                await ctx.respond(
                    "⏹️ Playback stopped and queue cleared.\n"
                    "🚪 Disconnected from voice channel."
                )
            else:
                await ctx.respond("❌ Failed to stop playback.")

        except Exception as e:
            logger.error(f"Error in stop command: {e}")
            await ctx.respond("❌ An unexpected error occurred.")


@music.register
class Skip(
    lightbulb.SlashCommand,
    name="skip",
    description="Skip the currently playing track.",
):
    """
    Skip the currently playing track.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Skip the current track.
        """
        try:
            guild_id = safe_guild_id(ctx)
            app = get_app_from_context(ctx)
            music_client = await get_music_client(app)

            if not music_client or not music_client.is_initialized:
                await ctx.respond("❌ Music client is not available.")
                return

            if not await music_client.is_playing(guild_id):
                await ctx.respond("❌ Nothing is currently playing.")
                return

            # Get current track info before skipping
            current_track = await music_client.get_current_track(guild_id)
            track_info = (
                f"{current_track.title} by {current_track.author}"
                if current_track
                else "Unknown track"
            )

            success = await music_client.skip(guild_id)
            if success:
                await ctx.respond(f"⏭️ Skipped: {track_info}")
            else:
                await ctx.respond("❌ Failed to skip track.")

        except Exception as e:
            logger.error(f"Error in skip command: {e}")
            await ctx.respond("❌ An unexpected error occurred.")


@music.register
class Queue(
    lightbulb.SlashCommand,
    name="queue",
    description="Show the current music queue.",
):
    """
    Display the current music queue.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Show the current queue.
        """
        try:
            guild_id = safe_guild_id(ctx)
            app = get_app_from_context(ctx)
            music_client = await get_music_client(app)

            if not music_client or not music_client.is_initialized:
                await ctx.respond("❌ Music client is not available.")
                return

            current_track = await music_client.get_current_track(guild_id)
            queue = await music_client.get_queue(guild_id)

            if not current_track and not queue:
                await ctx.respond("📜 The queue is empty.")
                return

            # Build queue display
            embed = hikari.Embed(title="🎵 Music Queue", color=hikari.Color(0x3498DB))

            # Current track
            if current_track:
                duration_minutes = current_track.duration // 60000
                duration_seconds = (current_track.duration % 60000) // 1000
                duration_str = f"{duration_minutes}:{duration_seconds:02d}"

                status = (
                    "⏸️ Paused"
                    if await music_client.is_paused(guild_id)
                    else "▶️ Playing"
                )
                embed.add_field(
                    name=f"{status} - Now Playing",
                    value=f"**{current_track.title}** by {current_track.author} [{duration_str}]",
                    inline=False,
                )

            # Queue
            if queue:
                queue_text = ""
                for i, queue_track in enumerate(queue[:10]):  # Show first 10 tracks
                    track = queue_track.track
                    duration_minutes = track.duration // 60000
                    duration_seconds = (track.duration % 60000) // 1000
                    duration_str = f"{duration_minutes}:{duration_seconds:02d}"

                    queue_text += f"`{i + 1}.` **{track.title}** by {track.author} [{duration_str}]\n"
                    queue_text += f"     👤 {queue_track.requester_name}\n"

                if len(queue) > 10:
                    queue_text += f"\n... and {len(queue) - 10} more tracks"

                embed.add_field(
                    name=f"📜 Up Next ({len(queue)} tracks)",
                    value=queue_text,
                    inline=False,
                )

                # Calculate total duration
                total_duration = sum(qt.track.duration for qt in queue)
                total_minutes = total_duration // 60000
                total_hours = total_minutes // 60
                total_minutes %= 60

                if total_hours > 0:
                    duration_display = f"{total_hours}h {total_minutes}m"
                else:
                    duration_display = f"{total_minutes}m"

                embed.set_footer(text=f"Total queue duration: {duration_display}")

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Error in queue command: {e}")
            await ctx.respond("❌ An unexpected error occurred.")


@music.register
class Volume(
    lightbulb.SlashCommand,
    name="volume",
    description="Set the playback volume.",
):
    """
    Set the playback volume (0-100).
    """

    level = lightbulb.integer(
        "level", "Volume level (0-100)", min_value=0, max_value=100
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Set the volume level.
        """
        try:
            guild_id = safe_guild_id(ctx)
            app = get_app_from_context(ctx)
            music_client = await get_music_client(app)

            if not music_client or not music_client.is_initialized:
                await ctx.respond("❌ Music client is not available.")
                return

            volume = self.level
            success = await music_client.set_volume(guild_id, volume)

            if success:
                await ctx.respond(f"🔊 Volume set to {volume}%")
            else:
                await ctx.respond("❌ Failed to set volume.")

        except Exception as e:
            logger.error(f"Error in volume command: {e}")
            await ctx.respond("❌ An unexpected error occurred.")


@music.register
class Disconnect(
    lightbulb.SlashCommand,
    name="disconnect",
    description="Disconnect the bot from the voice channel.",
):
    """
    Disconnect the bot from the voice channel and clear everything.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Disconnect from voice channel.
        """
        try:
            guild_id = safe_guild_id(ctx)
            app = get_app_from_context(ctx)
            music_client = await get_music_client(app)

            if not music_client or not music_client.is_initialized:
                await ctx.respond("❌ Music client is not available.")
                return

            success = await music_client.disconnect_from_voice(guild_id)
            if success:
                await ctx.respond("👋 Disconnected from voice channel.")
            else:
                await ctx.respond("❌ Failed to disconnect from voice channel.")

        except Exception as e:
            logger.error(f"Error in disconnect command: {e}")
            await ctx.respond("❌ An unexpected error occurred.")
