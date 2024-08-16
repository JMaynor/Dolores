"""
The basic module of functionality. Provides some simple randomization
functions for rolling dice.
"""

import json
import os
import random

from discord.ext import commands

with open(os.path.join("locales", "strings.json"), "r") as f:
    sarcastic_names = json.load(f).get("SARCASTIC_NAMES", [])


class rolling(commands.Cog):
    """
    Commands for rolling dice.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        description="A catch-all command for rolling any number of any-sided dice."
    )
    async def roll(self, ctx, *, dice_batches: str):
        """
        Rolls a dice in NdN format.
        Ex: /roll 5d10 3d8 2d4
        Dolores would roll 5 d10s, 3 d8s, 2 d4s and return the result of each.

        :param dice_batches: A string of dice rolls in NdN format.
        """
        await ctx.defer()
        final_formatted_rolls = []
        for dice_batch in dice_batches.split():
            try:
                rolls, limit = map(int, dice_batch.split("d"))
            except ValueError:
                break
            rolls_result = [str(random.randint(1, limit)) for r in range(rolls)]
            if len(rolls_result) > 500:
                await ctx.respond(
                    random.choice(
                        ["I ain't rollin all that for you...", "Absolutely not.", "No."]
                    )
                )
                return
            formatted_rolls = "(d" + str(limit) + ")  " + ", ".join(rolls_result)
            if limit != 20 and len(rolls_result) >= 3:
                formatted_rolls = (
                    formatted_rolls
                    + "    Sum: "
                    + str(sum([int(x) for x in rolls_result]))
                )
            final_formatted_rolls.append(formatted_rolls)
        if len(final_formatted_rolls) > 0:
            await ctx.respond("\n".join(final_formatted_rolls))
        else:
            await ctx.respond(
                f"Format has to be in NdN, {random.choice(sarcastic_names)}."
            )
            return

    @commands.slash_command(
        description="A catch-all command for rolling any number of any-sided dice. This one for DMs."
    )
    async def sroll(self, ctx, *, dice_batches: str):
        """
        Rolls a secret dice in NdN format.
        Ex: /sroll 5d10 3d8 2d4
        Dolores would roll 5 d10s, 3 d8s, 2 d4s and return the result of each.

        :param dice_batches: A string of dice rolls in NdN format.
        """
        await ctx.defer(ephemeral=True)
        final_formatted_rolls = []
        for dice_batch in dice_batches.split():
            try:
                rolls, limit = map(int, dice_batch.split("d"))
            except ValueError:
                break
            rolls_result = [str(random.randint(1, limit)) for r in range(rolls)]
            if len(rolls_result) > 500:
                await ctx.respond(
                    random.choice(
                        ["I ain't rollin all that for you...", "Absolutely not.", "No."]
                    ),
                    ephemeral=True,
                )
                return
            formatted_rolls = "(d" + str(limit) + ")  " + ", ".join(rolls_result)
            if limit != 20 and len(rolls_result) >= 3:
                formatted_rolls = (
                    formatted_rolls
                    + "    Sum: "
                    + str(sum([int(x) for x in rolls_result]))
                )
            final_formatted_rolls.append(formatted_rolls)
        if len(final_formatted_rolls) > 0:
            await ctx.respond("\n".join(final_formatted_rolls), ephemeral=True)
        else:
            await ctx.respond(
                f"Format has to be in NdN, {random.choice(sarcastic_names)}.",
                ephemeral=True,
            )
            return

    @commands.slash_command(
        description="For when you can't make a simple decision to save your life."
    )
    async def choose(self, ctx, *, choices: str):
        """
        Chooses between multiple choices.
        Ex: /choose "Kill the king" "Save the king" "Screw the King"
        Dolores would randomly choose one of the options you give her and return the result.

        :param choices: A string of choices separated by spaces.
        """
        await ctx.defer()
        await ctx.respond(random.choice(choices.split()))

    @commands.slash_command(
        description="Modified dice-roll command to roll a single d20. Short and sweet."
    )
    async def d20(self, ctx):
        """
        Rolls a single d20
        Ex: -d20
        Dolores rolls a single d20 and returns the result.
        """
        await ctx.defer()
        # 1 in million chance to roll a goon.
        if random.randint(1, 1000000) == 1:
            await ctx.respond("Goon.")
        await ctx.respond("(d20)  " + str(random.randint(1, 20)))

    @commands.slash_command(
        description="Modified dice-roll command to roll a single d20. Short and sweet. Also secret."
    )
    async def sd20(self, ctx):
        """
        Rolls a single d20
        Ex: /sd20
        Dolores rolls a single d20 and returns the result secretly.
        """
        await ctx.defer(ephemeral=True)
        await ctx.respond("(d20)  " + str(random.randint(1, 20)), ephemeral=True)
