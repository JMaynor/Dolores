"""
This module contains functionality relating to getting schedule info
from Notion.

Is intended to also have functionality for syncing schedule info
between Notion and Twitch. Not yet implemented.
"""

import json
import os
import random
import urllib.parse
from datetime import datetime

import discord
import requests
from discord.ext import commands

from modules.logger import logger

notion_headers = {
    "Authorization": "Bearer " + os.environ["NOTION_API_KEY"],
    "Notion-Version": os.environ["NOTION_VERSION"],
}

twitch_headers = {"Authorization": "", "Client-ID": os.environ["TWITCH_CLIENT_ID"]}

with open(os.path.join("..", "locales", "strings.json"), "r") as f:
    sarcastic_names = json.load(f).get("SARCASTIC_NAMES", [])


class Decorators:
    @staticmethod
    def refresh_twitch_token(decorated):
        """
        Decorator to refresh the Twitch token if it's expired.
        """

        def wrapper(self, *args, **kwargs):
            if "TWITCH_TOKEN_EXPIRES_AT" not in os.environ:
                pass
            else:
                pass
            return decorated(self, *args, **kwargs)

        wrapper.__name__ = decorated.__name__
        return wrapper


class scheduling(commands.Cog):
    """
    Commands for getting and writing schedule info.
    """

    def __init__(self, bot):
        self.bot = bot

    def get_notion_schedule(self, filter: dict, sorts: list):
        """
        Generic function that returns a given number of streams from the Notion schedule.
        Parameters: filter, sorts
        filters are a dict
        sorts are a list of dicts
        """
        json_data = {"filter": filter, "sorts": sorts}
        response = requests.post(
            os.environ["NOTION_BASE_URL"]
            + "databases/"
            + os.environ["NOTION_DATABASE_ID"]
            + "/query",
            headers=notion_headers,
            json=json_data,
            timeout=30,
        )
        if response.status_code != 200:
            logger.error(response.json())
            return ""
        else:
            return response.json()

    @Decorators.refresh_twitch_token
    def get_twitch_schedule(
        self, id=None, start_time=None, end_time=None, first=None, after=None
    ):
        """
        Gets schedule data from Twitch.
        """
        # Build the query string
        if id:
            id = "&id=" + id
        if start_time:
            start_time = "&start_time=" + start_time
        if end_time:
            end_time = "&end_time=" + end_time
        if first:
            first = "&first=" + first
        if after:
            after = "&after=" + after

        response = requests.get(
            os.environ["TWITCH_BASE_URL"]
            + "helix/schedule"
            + "?broadcaster_id="
            + os.environ["TWITCH_BROADCASTER_ID"]
            + start_time  # type: ignore
            + end_time
            + first
            + after,
            headers=twitch_headers,
            timeout=30,
        )

        if response.status_code != 200:
            logger.error(response.json())
            return ""

        return response.json()

    @Decorators.refresh_twitch_token
    def add_twitch_segment(self, start_time, is_recurring, category_id, title):
        """
        Adds a single segment to the Twitch schedule
        """
        json_data = {
            "start_time": start_time,
            "timezone": "America/Chicago",
            "duration": "240",
            "is_recurring": is_recurring,
            "category_id": category_id,
            "title": title,
        }

        response = requests.post(
            os.environ["TWITCH_BASE_URL"]
            + "helix/schedule/segment"
            + "?broadcaster_id="
            + os.environ["TWITCH_BROADCASTER_ID"],
            json=json_data,
            headers=twitch_headers,
        )

        if response.status_code != 200:
            logger.error(response.json())
            return ""

        return response.json()

    @Decorators.refresh_twitch_token
    def delete_twitch_segment(self, id):
        """
        Removes a single segment to the Twitch schedule
        Requires the segment ID
        """
        response = requests.delete(
            os.environ["TWITCH_BASE_URL"]
            + "helix/schedule/segment"
            + "?broadcaster_id="
            + os.environ["TWITCH_BROADCASTER_ID"]
            + "?id="
            + id,
            headers=twitch_headers,
        )

        if response.status_code != 204:
            logger.error(response.json())
            return ""

        return response.json()

    @Decorators.refresh_twitch_token
    def clear_twitch_schedule(self):
        """
        Clears the Twitch schedule of all segments
        """
        twitch_schedule = self.get_twitch_schedule()
        if twitch_schedule == "":
            return ""

        segment_ids = []
        for segment in twitch_schedule["data"]["segments"]:
            if "id" in segment:
                segment_ids.append(segment["id"])

        for segment_id in set(segment_ids):
            self.delete_twitch_segment(segment_id)

    @Decorators.refresh_twitch_token
    def search_twitch_categories(self, query):
        """
        Searches for Twitch categories
        """
        response = requests.get(
            os.environ["TWITCH_BASE_URL"]
            + "helix/search/categories"
            + "?query="
            + urllib.parse.quote(query),
            headers=twitch_headers,
        )

        if response.status_code != 200:
            logger.error(response.json())
            return ""

        return response.json()

    @commands.slash_command(
        description="Returns the next couple streams on the schedule."
    )
    async def schedule(self, ctx):
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
                + random.choice(sarcastic_names)
            )
            return

        embed = discord.Embed(
            title="Stream Schedule", description="Streams within the next week."
        )
        # Check for no streams
        if len(response["results"]) == 0:
            embed.add_field(
                name="Nada",
                value="We ain't got shit scheduled, " + random.choice(sarcastic_names),
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
