"""
text.py module
"""

import os
import random
import sys
from collections import deque

import discord
import openai
import requests
from discord.ext import commands

reply_method = os.environ["REPLY_METHOD"]

if reply_method == "openai":
    openai.api_key = os.environ["OPENAI_API_KEY"]

message_history = deque(maxlen=10)
system_messages = [
    {"role": "system", "content": x} for x in config["DISCORD"]["system_messages"]
]


class text(commands.Cog):
    """
    Commands for generating dialogue.
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

            # Generate a reply using the OpenAI API
            response = openai.chat.completions.create(
                model=config["OPENAI"]["model"],
                messages=system_messages + list(message_history),
                max_tokens=int(os.environ["MAX_TOKENS"]),
                temperature=config["OPENAI"]["temperature"],
                top_p=config["OPENAI"]["top_p"],
                frequency_penalty=config["OPENAI"]["frequency_penalty"],
                presence_penalty=config["OPENAI"]["presence_penalty"],
            )
            reply = response.choices[0].message.content
            # Add the reply to the message history
            message_history.append({"role": "assistant", "content": reply})

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
        return random.choice(config["DISCORD"]["snarky_comments"])

    def summarize_url(self, url):
        """
        Summarizes a given URL using the SMMRY API.
        """
        response = requests.post(
            os.environ["SMMRY_BASE_URL"]
            + "?SM_API_KEY="
            + os.environ["SMMRY_API_KEY"]
            + "&SM_QUOTE_AVOID="
            + os.environ["SMMRY_QUOTE_AVOID"].lower()
            + "&SM_LENGTH="
            + os.environ["SMMRY_LENGTH"]
            + "&SM_URL="
            + url
        )

        if response.status_code != 200:
            print(str(response.status_code), file=sys.stderr)
            return ""
        elif "sm_api_error" in response.json():
            print("Got error: ", response.json()["sm_api_error"], file=sys.stderr)
            return ""
        elif "sm_api_message" in response.json():
            print("Got message: " + response.json()["sm_api_message"], file=sys.stderr)
            return ""
        else:
            return response.json()

    @commands.slash_command(description="Summarizes a given URL using the SMMRY API.")
    async def summarize(self, ctx, *, url):
        """
        Summarizes a given URL using the SMMRY API.
        Ex: -summarize https://www.newsite.com/article
        Dolores would provide a brief summary of the article.
        """
        await ctx.defer()
        # Sanitize URL first, get rid of any query parameters
        url = url.split("?")[0]
        print("Summarizing URL: " + url)
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
