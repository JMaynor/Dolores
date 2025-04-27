"""
Hikari/Lightbulb version of the rolling module.
Provides randomization functions for rolling dice.
"""

import json
import logging
import os
import random

import hikari
import lightbulb

logger = logging.getLogger(__name__)

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjust path relative to this file if needed, assuming it's in src/modules/
    strings_path = os.path.join(current_dir, "..", "..", "locales", "strings.json")
    with open(strings_path, "r") as f:
        sarcastic_names = json.load(f).get(
            "SARCASTIC_NAMES", ["buddy"]
        )  # Default added
except FileNotFoundError:
    logger.warning(
        f"strings.json not found at {strings_path}. Using default sarcastic name."
    )
    sarcastic_names = ["buddy"]
except Exception as e:
    logger.error(f"Error loading strings.json: {e}. Using default sarcastic name.")
    sarcastic_names = ["buddy"]


loader = lightbulb.Loader()


@loader.command
class RollDice(
    lightbulb.SlashCommand, name="roll", description="Rolls dice in NdN format."
):
    """
    Rolls dice in NdN format.
    """

    dice_batches = lightbulb.string("dice_batches", "Dice to roll (e.g., 5d10 3d8 2d4)")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.defer()
        final_formatted_rolls = []
        dice_batches_str: str = self.dice_batches

        for dice_batch in dice_batches_str.split():
            try:
                rolls, limit = map(int, dice_batch.split("d"))
                if rolls <= 0 or limit <= 0:
                    raise ValueError("Number of rolls and limit must be positive.")
            except ValueError:
                logger.warning(
                    f"Invalid format in '{dice_batch}'. Expected NdN format."
                )
                await ctx.respond(
                    f"Invalid format in '{dice_batch}'. Use NdN format, {random.choice(sarcastic_names)}."
                )
                return  # Stop processing on first error

            if rolls > 500:  # Check before generating rolls
                await ctx.respond(
                    random.choice(
                        ["I ain't rollin all that for you...", "Absolutely not.", "No."]
                    )
                )
                return

            rolls_result = [str(random.randint(1, limit)) for _ in range(rolls)]

            formatted_rolls = f"(d{limit})  {', '.join(rolls_result)}"
            # Add sum for non-d20 rolls with 3+ dice
            if limit != 20 and rolls >= 3:
                try:
                    roll_sum = sum(int(x) for x in rolls_result)
                    formatted_rolls += f"    Sum: {roll_sum}"
                except ValueError:  # Should not happen if randint works
                    logger.error(
                        f"Error calculating sum for rolls: {rolls_result}. "
                        "This should not happen."
                    )
                    pass
            final_formatted_rolls.append(formatted_rolls)

        if final_formatted_rolls:
            response = "\n".join(final_formatted_rolls)
            # Discord message length limit is 2000 characters
            if len(response) > 2000:
                await ctx.respond("Result too long to display!")
            else:
                await ctx.respond(response)
        else:
            # This case should ideally be caught by the ValueError check earlier
            await ctx.respond(
                f"No valid dice batches provided. Format has to be in NdN, {random.choice(sarcastic_names)}."
            )


@loader.command
class SecretRollDice(
    lightbulb.SlashCommand,
    name="secret_roll",
    description="Rolls dice secretly (DM only).",
):
    """
    Rolls dice secretly (ephemeral, only to the user).
    """

    dice_batches = lightbulb.string("dice_batches", "Dice to roll (e.g., 5d10 3d8 2d4)")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.defer()
        final_formatted_rolls = []
        dice_batches_str: str = self.dice_batches

        for dice_batch in dice_batches_str.split():
            try:
                rolls, limit = map(int, dice_batch.split("d"))
                if rolls <= 0 or limit <= 0:
                    raise ValueError("Number of rolls and limit must be positive.")
            except ValueError:
                await ctx.respond(
                    f"Invalid format in '{dice_batch}'. Use NdN format, {random.choice(sarcastic_names)}.",
                    flags=hikari.MessageFlag.EPHEMERAL,
                )
                return

            if rolls > 500:
                await ctx.respond(
                    random.choice(
                        ["I ain't rollin all that for you...", "Absolutely not.", "No."]
                    ),
                    flags=hikari.MessageFlag.EPHEMERAL,
                )
                return

            rolls_result = [str(random.randint(1, limit)) for _ in range(rolls)]

            formatted_rolls = f"(d{limit})  {', '.join(rolls_result)}"
            if limit != 20 and rolls >= 3:
                try:
                    roll_sum = sum(int(x) for x in rolls_result)
                    formatted_rolls += f"    Sum: {roll_sum}"
                except ValueError:
                    pass
            final_formatted_rolls.append(formatted_rolls)

        if final_formatted_rolls:
            response = "\n".join(final_formatted_rolls)
            if len(response) > 2000:
                await ctx.respond(
                    "Result too long to display!", flags=hikari.MessageFlag.EPHEMERAL
                )
            else:
                await ctx.respond(response, flags=hikari.MessageFlag.EPHEMERAL)
        else:
            await ctx.respond(
                f"No valid dice batches provided. Format has to be in NdN, {random.choice(sarcastic_names)}.",
                flags=hikari.MessageFlag.EPHEMERAL,
            )


@loader.command
class Choose(
    lightbulb.SlashCommand,
    name="choose",
    description="Choose between multiple options.",
):
    """
    Choose between multiple options.
    """

    choices = lightbulb.string(
        "choices", "Choices separated by spaces (use quotes for multi-word choices)"
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.defer()
        choices_str: str = self.choices
        choice_list = choices_str.split()
        if not choice_list:
            await ctx.respond("You need to give me choices!")
            return
        await ctx.respond(random.choice(choice_list))


@loader.command
class Rolld20(lightbulb.SlashCommand, name="rolld20", description="Rolls a d20."):
    """
    Rolls a d20.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.defer()
        # 1 in million chance to roll a goon.
        if random.randint(1, 1000000) == 1:
            await ctx.respond("Goon.")
        else:
            await ctx.respond(f"(d20)  {random.randint(1, 20)}")


@loader.command
class SecretRolld20(
    lightbulb.SlashCommand, name="secret_rolld20", description="Rolls a d20 secretly."
):
    """
    Rolls a d20 secretly (ephemeral).
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.defer()
        if random.randint(1, 1000000) == 1:
            await ctx.respond("Goon.")
        else:
            await ctx.respond(
                f"(d20)  {random.randint(1, 20)}", flags=hikari.MessageFlag.EPHEMERAL
            )
