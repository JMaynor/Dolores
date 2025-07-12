"""
This module contains the Images cog for generating images
"""

import asyncio
import logging
import os
from typing import Literal

import hikari
import lightbulb
from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    AsyncOpenAI,
    RateLimitError,
)

logger = logging.getLogger(__name__)
loader = lightbulb.Loader()
async_openai_client = AsyncOpenAI()


class ImagePrompt(lightbulb.components.TextInput):
    """
    A text input for the image generation prompt.
    """

    def __init__(self) -> None:
        """
        Initialize prompt input
        """
        super().__init__(
            placeholder="Enter your prompt here...",
            custom_id="image_prompt",
            style=hikari.TextInputStyle.PARAGRAPH,
            max_length=1000,
            required=True,
            label="Image Prompt",
            min_length=1,
            value="",
        )


class ImageMenu(lightbulb.components.Menu):
    """
    A menu for the image generation command.
    Allows user to select, style, size, enter prompt.
    """

    def __init__(self) -> None:
        """
        Initialize menu
        """
        self.style = self.add_text_select(
            options=["natural", "vivid"],
            on_select=self.on_style_select,
            placeholder="Select style",
        )
        self.size = self.add_text_select(
            options=["1024x1024", "1792x1024", "1024x1792"],
            on_select=self.on_size_select,
            placeholder="Select size",
        )
        self.prompt = self.add(ImagePrompt())
        self.submit_button = self.add_interactive_button(
            hikari.ButtonStyle.PRIMARY, self.on_submit, label="Submit"
        )

    async def on_style_select(self, ctx: lightbulb.components.MenuContext) -> None:
        """
        Handle style selection
        """
        self.style = ctx.selected_values_for(self.style)
        logger.info(f"Style selected: {self.style}")

    async def on_size_select(self, ctx: lightbulb.components.MenuContext) -> None:
        """
        Handle size selection
        """
        self.size = ctx.selected_values_for(self.size)
        logger.info(f"Size selected: {self.size}")

    async def on_submit(self, ctx: lightbulb.components.MenuContext) -> None:
        """
        Handle form submission
        """
        prompt = self.prompt.value
        logger.info(f"Prompt submitted: {prompt}")
        # Trigger image generation with the selected options
        try:
            response = await async_openai_client.images.generate(
                prompt=prompt,
                model=os.environ["IMAGE_MODEL"],
                style=self.style,
                n=1,
                response_format="url",
                size=self.size,
                user=str(ctx.user.id),
            )
            if (
                not response.data
                or len(response.data) == 0
                or not hasattr(response.data[0], "url")
            ):
                logger.error("No image data returned from OpenAI API.")
                await ctx.respond("Sorry, I couldn't generate an image this time.")
                return
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
            embed = hikari.Embed()
            embed.description = prompt
            embed.set_image(image_url)
            await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(e)
            await ctx.respond(f"Error posting image to Discord: {e}.")


@loader.command
class Images(lightbulb.SlashCommand, name="images", description="Generate images"):
    """
    Generates an image based on a given prompt and posts as a reply.
    Ex: /generate_image A cat sitting on a table
    Dolores would generate an image of a cat sitting on a table.

    :param prompt: A string prompt for generating an image.
    """

    prompt = lightbulb.string("prompt", "Prompt for image generation")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        assert ctx.member is not None

        menu = ImageMenu()
        resp = await ctx.respond(
            "Please select the options for your image generation.",
            components=menu,
        )

        try:
            await menu.attach(ctx.client, timeout=60)
        except asyncio.TimeoutError:
            await ctx.edit_response(resp, "Image generation menu timed out.")
