"""
Fancy schmancy "AI" nonsense.
Module contains code that deals with text processing and image generation.
"""

import asyncio
import json
import os
import random
from collections import deque

import discord
import openai
import requests
from discord.ext import commands
from pydantic_ai import Agent

from modules._helpers import _basic_retry, _openai_retry
from modules.logger import logger

openai.api_key = os.environ["OPENAI_API_KEY"]

message_history = deque(maxlen=10)

# Construct the path to strings.json
current_dir = os.path.dirname(os.path.abspath(__file__))
strings_path = os.path.join(current_dir, "..", "..", "locales", "strings.json")
with open(strings_path, "r") as f:
    json_data = json.load(f)
    system_messages = json_data.get("LLM_SYSTEM_MESSAGES", [])
    # system_messages = [{"role": "system", "content": x} for x in system_messages]
    snarky_comments = json_data.get("SNARKY_COMMENTS", ["Whatever"])

# Set up agent
dol_agent = Agent(
    model="gpt-4o",
    system_prompt=system_messages,
    model_settings={
        "frequency_penalty": float(os.environ.get("FREQUENCY_PENALTY", 0.0)),
        "presence_penalty": float(os.environ.get("PRESENCE_PENALTY", 0.6)),
        "top_p": float(os.environ.get("TOP_P", 1.0)),
        "temperature": float(os.environ.get("TEMPERATURE", 0.9)),
        "max_tokens": int(os.environ.get("MAX_TOKENS", 150)),
    },
)


class generation(commands.Cog):
    """
    Commands for generating dialogue, summarization.
    """

    def __init__(self, bot):
        self.bot = bot

    @_openai_retry
    def generate_reply(self, person, message):
        """
        Generates a reply to a given message.
        """

        # Add the user's message to the message history
        message_history.append({"role": "user", "content": message, "name": person})

        try:
            # Generate a reply using the pydantic_ai Agent
            # The agent was already set up with the correct system prompts
            result = dol_agent.run_sync(
                user_prompt=message, message_history=list(message_history)
            )
            reply = result.data
            logger.info(f"Reply generated: {reply}")
            # Add the reply to the message history
            message_history.append({"role": "assistant", "content": reply})
        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            logger.error(f"Messages: {system_messages + list(message_history)}")
            if "APIConnectionError" in str(e):
                reply = "I'm sorry, I'm having trouble connecting to the API."
            elif "RateLimitError" in str(e):
                reply = (
                    "I'm sorry, I've reached my rate limit for now, try again later."
                )
            elif any(error in str(e) for error in ["APIStatusError", "APIError"]):
                reply = "I'm sorry, I'm having trouble with the API."
            else:
                reply = ""

        return reply

    @_openai_retry
    def generate_explanation(self, person, message):
        """
        Generates a simpler more informative explanation to a given message.
        """
        # Add the user's message to the message history
        message_history.append({"role": "user", "content": message, "name": person})

        message_history.append(
            {
                "role": "system",
                "content": "Attempt to explain the previous message if possible. Expand on what they are saying to provide a more informative response. Essentially, explain the contents of the message for somebody else who may not understand what the message is saying.",
            }
        )

        try:
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
            logger.info(f"Explanation generated: {reply}")
            # Add the reply to the message history
            message_history.append({"role": "assistant", "content": reply})
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            logger.error(f"Messages: {system_messages + list(message_history)}")
            reply = ""

        return reply

    def generate_snarky_comment(self):
        """
        Generates a snarky comment to be used when a user tries to use a command that does not exist.
        """
        return random.choice(snarky_comments)

    @_basic_retry
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
        try:
            response = requests.post(
                os.environ.get("SMMRY_BASE_URL", "https://api.smmry.com"),
                params=params,
            )
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Error {e.response.status_code}, could not summarize URL: {e}"
            )
            return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"Error, could not summarize URL: {e}")
            return ""

        if "sm_api_error" in response.json():
            logger.error(response.json()["sm_api_error"])
            return ""
        elif "sm_api_message" in response.json():
            logger.error(response.json()["sm_api_message"])
            return ""

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
        except openai.APIConnectionError as e:
            logger.error(f"Error connecting to the OpenAI API: {e}")
            ctx.respond("I'm sorry, I'm having trouble connecting to the OpenAI API.")
        except openai.RateLimitError as e:
            logger.error(f"Error with the OpenAI API rate limit: {e}")
            ctx.respond(
                "I'm sorry, I've reached my rate limit for now, try again later."
            )
        except (openai.APIStatusError, openai.APIError) as e:
            logger.error(f"Error with the OpenAI API: {e}")
            ctx.respond("I'm sorry, I'm having trouble with the OpenAI API.")
        except Exception as e:
            logger.error(e)
            await ctx.respond(f"Error generating image: {e}.")
            return

        # Add a delay to ensure the image is available
        # NOTE: Not sure if this is the issue. Image is getting generated, but is
        # inconsistently not being posted to Discord. Seems to have fixed though
        # so I will keep the delay there.
        await asyncio.sleep(1)

        try:
            embed = discord.Embed()
            embed.description = prompt
            embed.set_image(url=image_url)
            await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(e)
            await ctx.respond(f"Error posting image to Discord: {e}.")
