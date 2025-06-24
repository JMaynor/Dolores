"""
This module handles interacting with the lavalink server.
"""

import logging
import os
import time
from dataclasses import dataclass

import lavalink

logger = logging.getLogger(__name__)


@dataclass
class QueueTrack:
    """
    Represents a track in the queue with additional metadata.
    """

    track: lavalink.AudioTrack
    requester_id: int
    requester_name: str
    added_at: float


class MusicClient:
    """
    A lavalink client that handles music playbook with proper event filtering.
    """

    def __init__(self, bot):
        self.bot = bot
        self.lavalink = None
        self.queues = {}
        self.is_initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the lavalink client and wait for node connection.
        """
        try:
            host = os.getenv("LAVALINK_HOST", "localhost")
            port = int(os.getenv("LAVALINK_PORT", "2333"))
            password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

            bot_user = self.bot.get_me()
            if not bot_user:
                logger.error("Bot user not available yet")
                return False

            logger.info(f"Initializing lavalink client for {host}:{port}")

            self.lavalink = lavalink.Client(user_id=bot_user.id)

            # Add the node
            self.lavalink.add_node(
                host=host, port=port, password=password, region="us", name="default"
            )

            # Wait for node to be available (with timeout)
            import asyncio

            max_attempts = 10
            attempt = 0

            while attempt < max_attempts:
                if self.lavalink.node_manager.available_nodes:
                    logger.info("Lavalink node connected successfully")
                    break
                logger.info(
                    f"Waiting for lavalink node connection... (attempt {attempt + 1}/{max_attempts})"
                )
                await asyncio.sleep(1)
                attempt += 1

            if not self.lavalink.node_manager.available_nodes:
                logger.error("Failed to connect to lavalink node after 10 attempts")
                return False

            # Add event hooks with proper filtering
            self.lavalink.add_event_hook(self._on_track_start)
            self.lavalink.add_event_hook(self._on_track_end)
            self.lavalink.add_event_hook(self._on_track_exception)
            self.lavalink.add_event_hook(self._on_track_stuck)
            self.lavalink.add_event_hook(self._on_track_load_failed)
            self.lavalink.add_event_hook(self._on_websocket_closed)

            self.is_initialized = True
            logger.info(
                f"Lavalink client initialized successfully. Connected to {host}:{port}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize lavalink client: {e}")
            return False

    async def _on_track_load_failed(self, event) -> None:
        """
        Handle track load failed events.
        """
        if not hasattr(lavalink, "TrackLoadFailedEvent") or not isinstance(
            event, lavalink.TrackLoadFailedEvent
        ):
            return
        guild_id = int(getattr(event.player, "guild_id", 0))
        logger.error(
            f"Track load failed in guild {guild_id}: {getattr(event, 'exception', 'Unknown error')}"
        )

    async def _on_websocket_closed(self, event) -> None:
        """
        Handle websocket closed events.
        """
        if not hasattr(lavalink, "WebSocketClosedEvent") or not isinstance(
            event, lavalink.WebSocketClosedEvent
        ):
            return
        guild_id = int(getattr(event.player, "guild_id", 0))
        code = getattr(event, "code", "Unknown")
        reason = getattr(event, "reason", "Unknown")
        logger.warning(
            f"WebSocket closed in guild {guild_id}: code={code}, reason={reason}"
        )

    async def _on_track_start(self, event) -> None:
        """
        Handle track start events only
        """
        if not isinstance(event, lavalink.TrackStartEvent):
            return

        guild_id = int(event.player.guild_id)
        logger.info(f"Track started in guild {guild_id}: {event.track.title}")

    async def _on_track_end(self, event) -> None:
        """
        Handle track end events only
        """
        if not isinstance(event, lavalink.TrackEndEvent):
            return

        guild_id = int(event.player.guild_id)
        logger.info(f"Track ended in guild {guild_id}")
        # Play next track if available
        await self._play_next(guild_id)

    async def _on_track_exception(self, event) -> None:
        """
        Handle track exception events only
        """
        if not isinstance(event, lavalink.TrackExceptionEvent):
            return

        guild_id = int(event.player.guild_id)
        logger.error(f"Track exception in guild {guild_id}")
        await self._play_next(guild_id)

    async def _on_track_stuck(self, event) -> None:
        """
        Handle track stuck events only
        """
        if not isinstance(event, lavalink.TrackStuckEvent):
            return

        guild_id = int(event.player.guild_id)
        logger.warning(f"Track stuck in guild {guild_id}, skipping...")
        await self._play_next(guild_id)

    async def _play_next(self, guild_id: int) -> bool:
        """
        Play the next track in the queue.
        """
        if not self.is_initialized or not self.lavalink:
            return False

        player = self.lavalink.player_manager.get(guild_id)
        if not player:
            return False

        if guild_id not in self.queues or not self.queues[guild_id]:
            return False

        next_track = self.queues[guild_id].pop(0)
        try:
            await player.play(next_track.track)
            return True
        except Exception as e:
            logger.error(f"Failed to play next track: {e}")
            return await self._play_next(guild_id)

    async def connect_to_voice(self, guild_id: int, channel_id: int) -> bool:
        """
        Connect the bot to a voice channel.
        """
        if not self.is_initialized or not self.lavalink:
            return False
        try:
            await self.bot.update_voice_state(guild_id, channel_id)

            # Create player without endpoint - let voice events handle the connection details
            player = self.lavalink.player_manager.create(guild_id)

            # Set default volume to 100%
            await player.set_volume(100)

            # Initialize queue if not exists
            if guild_id not in self.queues:
                self.queues[guild_id] = []
            return True
        except Exception as e:
            logger.error(f"Failed to connect to voice channel: {e}")
            return False

    async def search_tracks(self, query: str):
        """
        Search for tracks.
        """
        if not self.is_initialized or not self.lavalink:
            return None
        try:
            if not (query.startswith("http://") or query.startswith("https://")):
                query = f"scsearch:{query}"
            logger.info(f"Searching for tracks with query: {query}")
            results = await self.lavalink.get_tracks(query)
            if results and results.tracks:
                logger.info(
                    f"Found {len(results.tracks)} tracks. First track: {results.tracks[0].title} by {results.tracks[0].author}"
                )
                logger.info(f"Track URI: {results.tracks[0].uri}")
                logger.info(f"Track duration: {results.tracks[0].duration}ms")
                return results.tracks
            else:
                logger.warning(f"No tracks found for query: {query}")
                return None
        except Exception as e:
            logger.error(f"Failed to search tracks: {e}")
            return None

    async def play_track(
        self, guild_id: int, track, requester_id: int, requester_name: str
    ) -> bool:
        """
        Play a track or add it to the queue.
        """
        if not self.is_initialized or not self.lavalink:
            return False

        player = self.lavalink.player_manager.get(guild_id)
        if not player:
            return False

        queue_track = QueueTrack(
            track=track,
            requester_id=requester_id,
            requester_name=requester_name,
            added_at=time.time(),
        )

        if guild_id not in self.queues:
            self.queues[guild_id] = []

        if not player.is_playing:
            try:
                # Wait until player is connected to the voice channel
                import asyncio

                max_attempts = 10
                attempt = 0
                while not player.is_connected and attempt < max_attempts:
                    logger.info(
                        f"Waiting for player to connect... (attempt {attempt + 1}/{max_attempts})"
                    )
                    await asyncio.sleep(0.5)
                    attempt += 1
                if not player.is_connected:
                    logger.error(
                        "Player is not connected to voice channel after waiting."
                    )
                    return False
                logger.info(f"Playing track directly. Volume: {player.volume}")
                logger.info(f"Player connected: {player.is_connected}")
                logger.info(
                    f"Player channel: {getattr(player, 'channel_id', 'Unknown')}"
                )
                logger.info(f"Track info: {track.title} - {track.uri}")
                await player.play(track)
                logger.info("Track play command sent successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to play track: {e}")
                return False
        else:
            self.queues[guild_id].append(queue_track)
            return True

    async def pause(self, guild_id: int) -> bool:
        """
        Pause playback.
        """
        if not self.is_initialized or not self.lavalink:
            return False
        player = self.lavalink.player_manager.get(guild_id)
        if not player:
            return False
        try:
            await player.set_pause(True)
            return True
        except Exception as e:
            logger.error(f"Failed to pause: {e}")
            return False

    async def resume(self, guild_id: int) -> bool:
        """
        Resume playback.
        """
        if not self.is_initialized or not self.lavalink:
            return False
        player = self.lavalink.player_manager.get(guild_id)
        if not player:
            return False
        try:
            await player.set_pause(False)
            return True
        except Exception as e:
            logger.error(f"Failed to resume: {e}")
            return False

    async def stop(self, guild_id: int) -> bool:
        """
        Stop playback and clear queue.
        """
        if not self.is_initialized or not self.lavalink:
            return False
        player = self.lavalink.player_manager.get(guild_id)
        if not player:
            return False
        try:
            await player.stop()
            if guild_id in self.queues:
                self.queues[guild_id].clear()
            return True
        except Exception as e:
            logger.error(f"Failed to stop: {e}")
            return False

    async def skip(self, guild_id: int) -> bool:
        """
        Skip the current track.
        """
        if not self.is_initialized or not self.lavalink:
            return False
        player = self.lavalink.player_manager.get(guild_id)
        if not player:
            return False
        try:
            await player.stop()
            return True
        except Exception as e:
            logger.error(f"Failed to skip: {e}")
            return False

    async def set_volume(self, guild_id: int, volume: int) -> bool:
        """
        Set the playback volume (0-100).
        """
        if not self.is_initialized or not self.lavalink:
            return False
        player = self.lavalink.player_manager.get(guild_id)
        if not player:
            return False
        try:
            await player.set_volume(volume)
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False

    async def disconnect_from_voice(self, guild_id: int) -> bool:
        """
        Disconnect from voice channel and clean up.
        """
        if not self.is_initialized or not self.lavalink:
            return False
        try:
            await self.bot.update_voice_state(guild_id, None)
            player = self.lavalink.player_manager.get(guild_id)
            if player:
                await player.stop()
                await self.lavalink.player_manager.destroy(guild_id)
            if guild_id in self.queues:
                self.queues[guild_id].clear()
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
            return False

    def is_playing(self, guild_id: int) -> bool:
        """
        Check if music is currently playing.
        """
        if not self.is_initialized or not self.lavalink:
            return False
        player = self.lavalink.player_manager.get(guild_id)
        return bool(player and player.is_playing)

    def is_paused(self, guild_id: int) -> bool:
        """
        Check if music is currently paused.
        """
        if not self.is_initialized or not self.lavalink:
            return False
        player = self.lavalink.player_manager.get(guild_id)
        return bool(player and player.paused)

    def get_current_track(self, guild_id: int):
        """
        Get the currently playing track.
        """
        if not self.is_initialized or not self.lavalink:
            return None
        player = self.lavalink.player_manager.get(guild_id)
        return player.current if player else None

    def get_queue(self, guild_id: int) -> list:
        """
        Get the queue for a guild.
        """
        return self.queues.get(guild_id, [])


# Global instance
music_client = None


async def get_music_client(bot):
    """
    Get or create the global music client instance.
    """
    global music_client

    if music_client is None:
        music_client = MusicClient(bot)
        if not await music_client.initialize():
            music_client = None

    return music_client
