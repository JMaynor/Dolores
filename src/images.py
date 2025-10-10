"""
This module contains the Images cog for generating images
"""

import asyncio
import logging
import os
from typing import Literal

import hikari
import lightbulb
from lightbulb.components import Modal, TextInput
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


class ImageGenerationModal(Modal):
    """
    Modal for collecting image generation parameters
    """

    def __init__(self) -> None:
        super().__init__()

        # Add text input for the prompt
        self.prompt_input: TextInput = self.add_paragraph_text_input(
            label="Image Prompt",
            placeholder="Describe the image you want to generate...",
            required=True,
            max_length=1000,
        )

        # Add text input for style selection
        self.style_input: TextInput = self.add_short_text_input(
            label="Style (natural or vivid)",
            placeholder="natural",
            required=False,
            max_length=10,
            value="natural",
        )

        # Add text input for size selection
        self.size_input: TextInput = self.add_short_text_input(
            label="Size (1024x1024, 1792x1024, 1024x1792)",
            placeholder="1792x1024",
            required=False,
            max_length=15,
            value="1792x1024",
        )

    async def on_submit(self, ctx: lightbulb.components.ModalContext) -> None:
        """
        Handle modal submission and generate the image
        """
        await ctx.defer()

        # Get values from the modal inputs
        prompt = ctx.value_for(self.prompt_input)
        if not prompt:
            await ctx.respond("Error: No prompt provided.")
            return

        style_input = (ctx.value_for(self.style_input) or "natural").lower()
        size_input = ctx.value_for(self.size_input) or "1792x1024"

        # Validate style
        style: Literal["natural", "vivid"] = "natural"
        if style_input == "vivid":
            style = "vivid"
        elif style_input not in ["natural", ""]:
            await ctx.respond(
                "Invalid style. Please use 'natural' or 'vivid'. Defaulting to 'natural'."
            )
            style = "natural"

        # Validate size
        valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
        if size_input not in valid_sizes:
            await ctx.respond(
                f"Invalid size. Please use one of: {', '.join(valid_sizes)}. Defaulting to '1792x1024'."
            )
            size_input = "1792x1024"

        try:
            response = await async_openai_client.images.generate(
                prompt=prompt,
                model=os.environ["IMAGE_MODEL"],
                style=style,
                n=1,
                response_format="url",
                size=size_input,  # type: ignore
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
            embed.description = (
                f"**Prompt:** {prompt}\n**Style:** {style}\n**Size:** {size_input}"
            )
            embed.set_image(image_url)
            await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(e)
            await ctx.respond(f"Error posting image to Discord: {e}.")


@loader.command
class Images(lightbulb.SlashCommand, name="images", description="Generate images"):
    """
    Opens a modal interface for generating images with customizable options.
    Users can specify prompt, style (natural/vivid), and size.
    """

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """
        Open the image generation modal
        """
        modal = ImageGenerationModal()
        custom_id = f"image_gen_{ctx.user.id}_{ctx.interaction.id}"

        try:
            # Send the modal response with components
            await ctx.respond_with_modal(
                title="Generate Image", custom_id=custom_id, components=modal
            )

            # Attach the modal to the client to listen for submissions
            client = ctx.client
            await modal.attach(client, custom_id, timeout=300.0)  # 5 minute timeout

        except asyncio.TimeoutError:
            logger.warning(f"Image generation modal timed out for user {ctx.user.id}")
        except Exception as e:
            logger.error(f"Error with image generation modal: {e}")
            await ctx.respond(f"Error with image generation: {e}", ephemeral=True)
