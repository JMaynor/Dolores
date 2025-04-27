"""
Fancy schmancy "AI" nonsense.
Module contains code that deals with generating text responses using an LLM.
"""

import json
import logging
import os
import random
from collections import deque

from pydantic_ai import Agent

logger = logging.getLogger(__name__)


class chat:
    """
    Commands for generating dialogue.
    """

    def __init__(self):
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

        self.dol_agent = Agent(
            name="Dolores",
            model=os.environ["LLM_MODEL"],  # type: ignore
            system_prompt=self.system_messages,
            model_settings={
                "frequency_penalty": float(os.environ.get("FREQUENCY_PENALTY", 0.0)),
                "presence_penalty": float(os.environ.get("PRESENCE_PENALTY", 0.6)),
                "top_p": float(os.environ.get("TOP_P", 1.0)),
                "temperature": float(os.environ.get("TEMPERATURE", 0.9)),
                "max_tokens": int(os.environ.get("MAX_TOKENS", 150)),
            },
        )

    async def generate_reply(self, person: str, message: str) -> str:
        """
        Generates a reply to a given message

        :param person: The person who sent the message (Note: pydantic_ai doesn't directly use this 'person' param in history yet)
        :param message: The message to reply to
        :return: The generated reply text
        """
        reply_text = ""
        try:
            # Pass the current history (list of ModelMessage objects)
            run = await self.dol_agent.run(
                user_prompt=message, message_history=list(self.message_history)
            )
            reply_text = run.data  # Get the primary text response
            logger.info(f"Reply generated: {reply_text}")

            # Update history with the new messages from this run
            # run.new_messages() typically contains [UserPromptPart(...), TextPart(...)]
            new_messages = run.new_messages()
            self.message_history.extend(new_messages)

        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            # Log history if error occurs (history contains ModelMessage objects now)
            logger.error(f"Current message history: {list(self.message_history)}")
            reply_text = "I'm sorry, I encountered an error while generating a reply."

        return reply_text

    async def generate_explanation(self, person: str, message: str) -> str:
        """
        Generates a simpler more informative explanation to a given message

        :param person: The person who sent the message (Note: pydantic_ai doesn't directly use this 'person' param in history yet)
        :param message: The message to explain
        :return: The generated explanation text
        """
        explanation_text = ""
        explanation_prompt = f"Please explain the following message in a simpler, more informative way, as if for someone who might not understand the context or jargon: '{message}'"

        try:
            # Pass the current history (list of ModelMessage objects)
            run = await self.dol_agent.run(
                user_prompt=explanation_prompt,
                message_history=list(self.message_history),
            )
            explanation_text = run.data
            logger.info(f"Explanation generated: {explanation_text}")

            # Update history with the new messages from this run
            new_messages = run.new_messages()
            self.message_history.extend(new_messages)

        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            # Log history if error occurs (history contains ModelMessage objects now)
            logger.error(f"Current message history: {list(self.message_history)}")
            explanation_text = (
                "I'm sorry, I encountered an error while generating an explanation."
            )

        return explanation_text  # Return the extracted text

    async def generate_snarky_comment(self) -> str:
        """
        Generates a snarky comment to be used when a user tries to
        use a command that does not exist.
        """
        return random.choice(self.snarky_comments)
