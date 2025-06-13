"""
This module contains functionality relating to getting schedule info
from Notion.

Is intended to also have functionality for syncing schedule info
between Notion and Twitch. Not yet implemented.
"""

import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path

import hikari
import lightbulb
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

try:
    current_dir = Path(__file__).resolve().parent
    strings_path = current_dir.parent.parent / "locales" / "strings.json"
    with open(strings_path, "r") as f:
        sarcastic_names = json.load(f).get("SARCASTIC_NAMES", ["buddy"])
except Exception as e:
    logger.warning(f"Could not load sarcastic names: {e}. Using default.")
    sarcastic_names = ["buddy"]


loader = lightbulb.Loader()


@loader.command
class Schedule(lightbulb.SlashCommand, name="schedule", description="Get the schedule"):
    """
    Returns streams scheduled for the next week.
    """

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
        ),
    )
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
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error, could not get schedule data: {e}")
            return ""

        return response.json()

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
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

        embed = hikari.Embed(
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
