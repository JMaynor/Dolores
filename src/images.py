"""
This module contains the Images cog for generating images.
"""

import asyncio
import logging
from typing import Literal

import hikari
import lightbulb
from lightbulb.components import Modal, TextInput
from pydantic_ai import Agent
from pydantic_ai.messages import BinaryImage

logger = logging.getLogger(__name__)
loader = lightbulb.Loader()


class ImageGenerationModal(Modal):
    """
    Modal for collecting image generation parameters.
    """

    def __init__(self) -> None:
        """
        Initialize the modal with input fields.
        """
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
        Handle modal submission and generate the image.
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
            agent = Agent("openai-responses:gpt-5", output_type=BinaryImage)

            result = agent.run_sync()

            output = result.output
            assert isinstance(output, BinaryImage)
            assert output.media_type == "image/png"
            assert isinstance(output.data, bytes)
            assert result.response.images == [output]
            with open("axolotl-openai.png", "wb") as f:
                f.write(output.data)
        except Exception as e:
            logger.error(f"")

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
        Open the image generation modal.
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
