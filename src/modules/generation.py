"""
Fancy schmancy "AI" nonsense.
Module contains code that deals with text processing and image generation.
"""

import json
import os
import random
import sys
from collections import deque

import discord
import openai
import requests
from discord.ext import commands

from modules.logger import logger

reply_method = os.environ["REPLY_METHOD"]

if reply_method == "openai":
    openai.api_key = os.environ["OPENAI_API_KEY"]

message_history = deque(maxlen=10)

# Construct the path to strings.json
current_dir = os.path.dirname(os.path.abspath(__file__))
strings_path = os.path.join(current_dir, "..", "..", "locales", "strings.json")
with open(strings_path, "r") as f:
    json_data = json.load(f)
    system_messages = json_data.get("LLM_SYSTEM_MESSAGES", [""])
    snarky_comments = json_data.get("SNARKY_COMMENTS", [""])


class generation(commands.Cog):
    """
    Commands for generating dialogue, summarization.
    """

    def __init__(self, bot):
        self.bot = bot

    def generate_reply(self, message):
        """
        Generates a reply to a given message. Currently using chatterbot. Intent is to use a proper LLM in the future.
        """
        if reply_method == "openai":
            # Add the user's message to the message history
            message_history.append({"role": "user", "content": message})

            try:
                # Generate a reply using the OpenAI API
                response = openai.chat.completions.create(
                    model=os.environ["OPENAI_MODEL"],
                    messages=system_messages + list(message_history),
                    max_tokens=int(os.environ.get("MAX_TOKENS", 150)),
                    temperature=float(os.environ.get("TEMPERATURE", 0.9)),
                    top_p=float(os.environ.get("TOP_P", 1.0)),
                    frequency_penalty=float(os.environ.get("FREQUENCY_PENALTY", 0.0)),
                    presence_penalty=float(os.environ.get("PRESENCE_PENALTY", 0.6)),
                )
                reply = response.choices[0].message.content
                logger.info(f"Reply generated: {reply}")
                # Add the reply to the message history
                message_history.append({"role": "assistant", "content": reply})
            except Exception as e:
                logger.error(f"Error generating reply: {e}")
                logger.error(f"Messages: {system_messages + list(message_history)}")

        # Use a self-hosted LLM to generate a reply
        elif reply_method == "self":
            reply = ""
        # If reply method not specified, return empty string
        else:
            reply = ""

        return reply

    def generate_snarky_comment(self):
        """
        Generates a snarky comment to be used when a user tries to use a command that does not exist.
        """
        return random.choice(snarky_comments)

    def summarize_url(self, url):
        """
        Summarizes a given URL using the SMMRY API.
        """
        params = {
            "SM_API_KEY": os.environ["SMMRY_API_KEY"],
            "SM_QUOTE_AVOID": os.environ.get("SMMRY_QUOTE_AVOID", "true").lower(),
            "SM_LENGTH": os.environ["SMMRY_LENGTH"],
            "SM_URL": url,
        }
        response = requests.post(
            os.environ.get("SMMRY_BASE_URL", "https://api.smmry.com"),
            params=params,
        )

        if response.status_code != 200:
            logger.error(response.json())
            return ""
        elif "sm_api_error" in response.json():
            logger.error(response.json()["sm_api_error"])
            return ""
        elif "sm_api_message" in response.json():
            logger.error(response.json()["sm_api_message"])
            return ""
        else:
            return response.json()

    @commands.slash_command(description="Summarizes a given URL using the SMMRY API.")
    async def summarize(self, ctx, *, url):
        """
        Summarizes a given URL using the SMMRY API.
        Ex: /summarize https://www.newsite.com/article
        Dolores would provide a brief summary of the article.

        :param url: A URL to summarize.
        """
        await ctx.defer()
        # Sanitize URL first, get rid of any query parameters
        url = url.split("?")[0]
        logger.info("Summarizing URL: " + url)
        response = self.summarize_url(url)
        if response == "":
            await ctx.respond("Unable to summarize that URL.")
            return
        if "sm_api_title" in response:
            embed_title = response["sm_api_title"]
        else:
            embed_title = "Summary"
        embed = discord.Embed(title=embed_title)
        embed.add_field(name="Article Summary", value=response["sm_api_content"])
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Generates an image based on a given prompt.")
    async def generate_image(self, ctx, *, prompt: str):
        """
        Generates an image based on a given prompt and posts as a reply.
        Ex: /generate_image A cat sitting on a table
        Dolores would generate an image of a cat sitting on a table.

        :param prompt: A string prompt for generating an image.
        """
        await ctx.defer()
        if os.environ["OPENAI_API_KEY"] == "":
            await ctx.respond("No OpenAI API key found.")

        try:
            style = os.environ.get("IMAGE_STYLE", None)
            if style not in ["natural", "vivid"]:
                style = "natural"
            response = openai.images.generate(
                prompt=prompt,
                model=os.environ["OPENAI_IMAGE_MODEL"],
                style=style,
                n=1,
                response_format="url",
                size="1792x1024",
                user=str(ctx.author.id),
            )
            image_url = response.data[0].url
            logger.info(f"Generated image URL: {image_url}")
        except Exception as e:
            logger.error(e)
            await ctx.respond(f"Error generating image: {e}.")

        try:
            embed = discord.Embed()
            embed.description = prompt
            embed.set_image(url=image_url)
            await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(e)
            await ctx.respond(f"Error posting image to Discord: {e}.")
