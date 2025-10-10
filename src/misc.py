"""
Misclellaneous whatever commands for Dolores. Will not have any dependencies.
"""

import lightbulb

loader = lightbulb.Loader()


@loader.command
class Bingy(lightbulb.SlashCommand, name="bingy", description="Bingy"):
    """
    A command that replies with Bingy to a user when they call it.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond("Bingy")
