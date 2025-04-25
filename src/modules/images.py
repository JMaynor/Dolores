"""
This module contains the Images cog for generating images
"""

import asyncio
import os
from typing import Literal

import discord
from discord.ext import commands
from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    AsyncOpenAI,
    RateLimitError,
)

from modules._logger import logger


class images(commands.Cog):
    """
    Commands for generating images.
    """

    def __init__(self, bot):
        self.bot = bot
        self.async_openai_client = AsyncOpenAI()

    @commands.slash_command(description="Generates an image based on a given prompt.")
    async def generate_image(self, ctx, *, prompt: str):
        """
        Generates an image based on a given prompt and posts as a reply.
        Ex: /generate_image A cat sitting on a table
        Dolores would generate an image of a cat sitting on a table.

        :param prompt: A string prompt for generating an image.
        """
        await ctx.defer()

        try:
            style_input = os.environ.get("IMAGE_STYLE", "natural").lower()
            style: Literal["natural", "vivid"] = "natural"
            if style_input == "vivid":
                style = "vivid"

            response = await self.async_openai_client.images.generate(
                prompt=prompt,
                model=os.environ["IMAGE_MODEL"],
                style=style,
                n=1,
                response_format="url",
                size="1792x1024",
                user=str(ctx.author.id),
            )
            image_url = response.data[0].url
            logger.info(f"Generated image URL: {image_url}")
        except APIConnectionError as e:
            logger.error(f"Error connecting to the OpenAI API: {e}")
            await ctx.respond(
                "I'm sorry, I'm having trouble connecting to the OpenAI API."
            )
            return
        except RateLimitError as e:
            logger.error(f"Error with the OpenAI API rate limit: {e}")
            await ctx.respond(
                "I'm sorry, I've reached my rate limit for now, try again later."
            )
            return
        except (APIStatusError, APIError) as e:
            logger.error(f"Error with the OpenAI API: {e}")
            await ctx.respond("I'm sorry, I'm having trouble with the OpenAI API.")
            return
        except Exception as e:
            logger.error(e)
            await ctx.respond(f"Error generating image: {e}.")
            return

        await asyncio.sleep(1)

        try:
            embed = discord.Embed()
            embed.description = prompt
            embed.set_image(url=image_url)
            await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(e)
            await ctx.respond(f"Error posting image to Discord: {e}.")
