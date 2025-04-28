"""
Module contains code that deals with playing audio in voice channels.
Much has come directly from the pomice example bot so most of module relies on
having a lavalink server running.
"""

import asyncio
import logging
import math
import os

import hikari
import lightbulb

logger = logging.getLogger(__name__)

loader = lightbulb.Loader()


@loader.command
class Music(
    lightbulb.SlashCommand,
    name="music",
    description="Commands related to playing audio.",
):
    """
    Controls audio playback in voice channels.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Placeholder
        """
        pass
