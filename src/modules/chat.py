"""
Fancy schmancy "AI" nonsense.
Module contains code that deals with generating text responses using an LLM.
"""

import json
import os
import random
from collections import deque

from discord.ext import commands
from pydantic_ai import Agent

from modules._logger import logger


class chat(commands.Cog):
    """
    Commands for generating dialogue.
    """

    def __init__(self, bot):
        self.bot = bot
        self.message_history = deque(maxlen=10)

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
            self.json_data = json.load(f)
            self.system_messages = self.json_data.get("LLM_SYSTEM_MESSAGES", [])
            self.snarky_comments = self.json_data.get("SNARKY_COMMENTS", ["Whatever"])

        # Set up LLM agent
        self.dol_agent = Agent(
            name="Dolores",
            model=os.environ.get("LLM_MODEL", "gpt-4o"),  # type: ignore
            system_prompt=self.system_messages,
            model_settings={
                "frequency_penalty": float(os.environ.get("FREQUENCY_PENALTY", 0.0)),
                "presence_penalty": float(os.environ.get("PRESENCE_PENALTY", 0.6)),
                "top_p": float(os.environ.get("TOP_P", 1.0)),
                "temperature": float(os.environ.get("TEMPERATURE", 0.9)),
                "max_tokens": int(os.environ.get("MAX_TOKENS", 150)),
            },
        )

    def generate_reply(self, person: str, message: str) -> str:
        """
        Generates a reply to a given message

        :param person: The person who sent the message
        :param message: The message to reply to
        :return: The generated reply
        """
        # Add the user's message to the message history as a string
        self.message_history.append(message)

        try:
            # Generate a reply using the pydantic_ai Agent
            result = self.dol_agent.run_sync(
                user_prompt=message, message_history=list(self.message_history)
            )
            reply = result.data
            logger.info(f"Reply generated: {reply}")

            # Add the reply to the message history
            self.message_history.append(reply)

        except Exception as e:
            logger.error(f"Error generating reply with pydantic-ai: {e}")
            logger.error(f"Current message history: {list(self.message_history)}")
            reply = "I'm sorry, I encountered an error while generating a reply."

        return reply

    def generate_explanation(self, person: str, message: str) -> str:
        """
        Generates a simpler more informative explanation to a given message

        :param person: The person who sent the message
        :param message: The message to explain
        :return: The generated explanation
        """
        # Add the user's message to the message history
        self.message_history.append(message)

        # Construct a prompt that asks the agent to explain the last message
        explanation_prompt = f"Please explain the following message in a simpler, more informative way, as if for someone who might not understand the context or jargon: '{message}'"

        try:
            # Use the agent to generate the explanation
            result = self.dol_agent.run_sync(
                user_prompt=explanation_prompt,
                message_history=list(self.message_history),
            )
            explanation = result.data
            logger.info(f"Explanation generated: {explanation}")
            # Add the explanation to the message history
            self.message_history.append(explanation)
        except Exception as e:
            logger.error(f"Error generating explanation with pydantic-ai: {e}")
            logger.error(f"Current message history: {list(self.message_history)}")
            explanation = (
                "I'm sorry, I encountered an error while generating an explanation."
            )

        return explanation

    def generate_snarky_comment(self) -> str:
        """
        Generates a snarky comment to be used when a user tries to
        use a command that does not exist.
        """
        return random.choice(self.snarky_comments)
