# rolling_hikari.py
"""
Hikari/Lightbulb version of the rolling module.
Provides randomization functions for rolling dice.
"""

import json
import os
import random

import hikari
import lightbulb

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjust path relative to this file if needed, assuming it's in src/modules/
    strings_path = os.path.join(current_dir, "..", "..", "locales", "strings.json")
    with open(strings_path, "r") as f:
        sarcastic_names = json.load(f).get(
            "SARCASTIC_NAMES", ["buddy"]
        )  # Default added
except FileNotFoundError:
    print(
        f"Warning: strings.json not found at {strings_path}. Using default sarcastic name."
    )
    sarcastic_names = ["buddy"]
except Exception as e:
    print(f"Error loading strings.json: {e}")
    sarcastic_names = ["buddy"]


rolling = lightbulb.Group("rolling", "Rolling commands group")


@rolling.commands
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


# --- Secret Roll Command ---
@roll_group.command
@lightbulb.option("dice_batches", "Dice to roll secretly (e.g., 5d10 3d8)", str)
@lightbulb.command("secret_dice", "Rolls dice secretly (DM only).")
@lightbulb.implements(lightbulb.SlashCommand)
async def sroll_dice(ctx: lightbulb.Context) -> None:
    """Rolls dice secretly."""
    await ctx.defer(flags=hikari.MessageFlag.EPHEMERAL)
    final_formatted_rolls = []
    dice_batches_str: str = ctx.options.dice_batches

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


# --- Choose Command (Standalone) ---
@plugin.command
@lightbulb.option(
    "choices", "Choices separated by spaces (use quotes for multi-word choices)", str
)
@lightbulb.command("choose", "For when you can't make a simple decision.")
@lightbulb.implements(lightbulb.SlashCommand)
async def choose(ctx: lightbulb.Context) -> None:
    """Chooses between multiple choices."""
    await ctx.defer()
    # Lightbulb might parse quoted strings as single arguments,
    # but splitting by space is the original behavior.
    # Consider using multiple options or a converter for more robust parsing if needed.
    choices_str: str = ctx.options.choices
    choice_list = choices_str.split()
    if not choice_list:
        await ctx.respond(
            "You need to give me choices!", flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    await ctx.respond(random.choice(choice_list))


# --- d20 Command ---
@roll_group.command
@lightbulb.command("d20", "Rolls a single d20.")
@lightbulb.implements(lightbulb.SlashCommand)
async def roll_d20(ctx: lightbulb.Context) -> None:
    """Rolls a single d20."""
    await ctx.defer()
    # 1 in million chance to roll a goon.
    if random.randint(1, 1000000) == 1:
        await ctx.respond("Goon.")
    else:
        await ctx.respond(f"(d20)  {random.randint(1, 20)}")


# --- Secret d20 Command ---
@roll_group.command
@lightbulb.command("secret_d20", "Rolls a single d20 secretly.")
@lightbulb.implements(lightbulb.SlashCommand)
async def sroll_d20(ctx: lightbulb.Context) -> None:
    """Rolls a single d20 secretly."""
    await ctx.defer(flags=hikari.MessageFlag.EPHEMERAL)
    # No goon check for secret rolls? (Following original logic)
    await ctx.respond(
        f"(d20)  {random.randint(1, 20)}", flags=hikari.MessageFlag.EPHEMERAL
    )


# --- Required load/unload functions for Lightbulb extensions ---
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
    print("Rolling plugin loaded.")


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
    print("Rolling plugin unloaded.")
