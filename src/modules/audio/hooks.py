"""
Hooks for checking voice state and player status
"""

import lightbulb


class PlayerNotPlaying(RuntimeError):
    pass


class PlayerNotConnected(RuntimeError):
    pass


class NotInVoice(RuntimeError):
    pass


class NotSameVoice(RuntimeError):
    pass


@lightbulb.hook(lightbulb.ExecutionSteps.CHECKS)
async def valid_user_voice(
    pipeline: lightbulb.ExecutionPipeline, ctx: lightbulb.Context
) -> None:
    """Hook to check if the user is in a valid voice state."""
    if not ctx.guild_id:
        raise RuntimeError("Cannot invoke command in DMs")

    # Fetch voice states using hikari cache
    states = ctx.app.cache.get_voice_states_view_for_guild(ctx.guild_id)
    user_voice_state = states.get(ctx.author.id)
    bot_voice_state = states.get(ctx.app.get_me().id)

    if not user_voice_state or not user_voice_state.channel_id:
        raise NotInVoice("Join a voice channel to use this command.")

    if (
        bot_voice_state
        and bot_voice_state.channel_id
        is not None  # Ensure bot is actually in a channel
        and user_voice_state.channel_id != bot_voice_state.channel_id
    ):
        raise NotSameVoice(
            "Join the same voice channel as the bot to use this command."
        )
    # If checks pass, return None implicitly


@lightbulb.hook(lightbulb.ExecutionSteps.CHECKS)
async def player_connected(
    pipeline: lightbulb.ExecutionPipeline, ctx: lightbulb.Context
) -> None:
    """Hook to check if the Lavalink player is connected."""
    # Ensure guild_id exists (though check_valid_user_voice likely runs first)
    if not ctx.guild_id:
        raise RuntimeError("Cannot check player connection in DMs")

    # Access Lavalink instance (assuming it's stored in bot.d.lavalink)
    if not hasattr(ctx.app.d, "lavalink"):
        raise RuntimeError("Lavalink component not found on bot.")

    player = ctx.app.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_connected:
        raise PlayerNotConnected("Bot is not connected to any voice channel.")
    # If check passes, return None implicitly


@lightbulb.hook(lightbulb.ExecutionSteps.CHECKS)
async def player_playing(
    pipeline: lightbulb.ExecutionPipeline, ctx: lightbulb.Context
) -> None:
    """Hook to check if the Lavalink player is currently playing."""
    if not ctx.guild_id:
        raise RuntimeError("Cannot check player status in DMs")

    if not hasattr(ctx.app.d, "lavalink"):
        raise RuntimeError("Lavalink component not found on bot.")

    player = ctx.app.d.lavalink.player_manager.get(ctx.guild_id)
    # PlayerConnected hook likely runs first, but double-check player existence
    if not player or not player.is_playing:
        raise PlayerNotPlaying("Player is not currently playing anything.")
    # If check passes, return None implicitly
