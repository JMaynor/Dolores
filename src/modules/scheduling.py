"""
This module contains functionality relating to getting schedule info
from Notion.

Is intended to also have functionality for syncing schedule info
between Notion and Twitch. Not yet implemented.
"""

import json
import os
import random
from datetime import datetime

import discord
import requests
from discord.ext import commands
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from modules._logger import logger

_basic_retry = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ),
)


class scheduling(commands.Cog):
    """
    Commands for getting and writing schedule info.
    """

    def __init__(self, bot):
        self.bot = bot

        # Construct the path to strings.json
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "..",
                "locales",
                "strings.json",
            ),
            "r",
        ) as f:
            self.sarcastic_names = json.load(f).get("SARCASTIC_NAMES", [])

    @_basic_retry
    def get_notion_schedule(self, filter: dict, sorts: list):
        """
        Generic function that returns a given number of streams from the Notion schedule.
        Parameters: filter, sorts
        filters are a dict
        sorts are a list of dicts
        """
        json_data = {"filter": filter, "sorts": sorts}
        try:
            response = requests.post(
                os.environ["NOTION_BASE_URL"]
                + "databases/"
                + os.environ["NOTION_DATABASE_ID"]
                + "/query",
                headers={
                    "Authorization": "Bearer " + os.environ["NOTION_API_KEY"],
                    "Notion-Version": os.environ["NOTION_VERSION"],
                },
                json=json_data,
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Error {e.response.status_code}, could not get schedule data: {e}"
            )
            return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"Error, could not get schedule data: {e}")
            return ""

        return response.json()

    @commands.slash_command(
        description="Returns the next couple streams on the schedule."
    )
    async def schedule(self, ctx: discord.commands.context.ApplicationContext):
        """
        Returns any streams scheduled for the next week.
        Ex: /schedule
        Dolores will return an embed of stream dates, names, and people.
        """
        await ctx.defer()

        filter = {"property": "Date", "date": {"next_week": {}}}
        sorts = [{"property": "Date", "direction": "ascending"}]

        response = self.get_notion_schedule(filter, sorts)

        if response == "":
            await ctx.respond(
                "Notion's API is giving me an error, so I couldn't get that for you, "
                + random.choice(self.sarcastic_names)
            )
            return

        embed = discord.Embed(
            title="Stream Schedule", description="Streams within the next week."
        )
        # Check for no streams
        if len(response["results"]) == 0:
            embed.add_field(
                name="Nada",
                value="We ain't got shit scheduled, "
                + random.choice(self.sarcastic_names),
            )
        else:
            for elem in response["results"]:
                try:
                    date = elem["properties"]["Date"]["date"]["start"]
                    date_weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
                except:
                    date = ""
                    date_weekday = ""
                try:
                    title = elem["properties"]["Name"]["title"][0]["plain_text"]
                except:
                    title = ""
                try:
                    people = ", ".join(
                        [
                            person["name"]
                            for person in elem["properties"]["Tags"]["multi_select"]
                        ]
                    )
                except:
                    people = ""

                embed.add_field(
                    name=date + " " + date_weekday,
                    value=title + "   (" + people + ")",
                    inline=False,
                )
        await ctx.respond(embed=embed)
