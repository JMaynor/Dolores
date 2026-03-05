"""
Fancy schmancy "AI" nonsense.
Module contains code that deals with generating text responses using an LLM.
"""

import logging
import os
import random
from collections import deque

from pydantic_ai import Agent

from src.constants import LLM_SYSTEM_MESSAGES, SNARKY_COMMENTS

logger = logging.getLogger(__name__)


class Chat:
    """
    Commands for generating dialogue.
    """

    def __init__(self) -> None:
        """
        Initializes the chat agent and message history.
        """
        self.message_history = deque(maxlen=10)

        self.dol_agent = Agent(
            name="Dolores",
            model=os.environ["LLM_MODEL"],
            system_prompt=LLM_SYSTEM_MESSAGES,
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
        Generates a reply to a given message.

        :param person: The person who sent the message (Note: pydantic_ai doesn't directly use this 'person' param in history yet)
        :param message: The message to reply to
        :return: The generated reply text
        """
        reply_text = ""

        logger.debug(f"Generating reply for: {person}")

        # Is there a way to determine whether the user is asking for an image to be generated?

        try:
            # Pass the current history (list of ModelMessage objects)
            run = await self.dol_agent.run(
                user_prompt=message, message_history=list(self.message_history)
            )
            reply_text = run.output  # Get the primary text response
            logger.info(f"Reply generated: {reply_text}")

            # Update history with the new messages from this run
            # run.new_messages() typically contains [UserPromptPart(...), TextPart(...)]
            new_messages = run.new_messages()
            self.message_history.extend(new_messages)

        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            # Log history if error occurs (history contains ModelMessage objects now)
            logger.error(f"Current message history: {list(self.message_history)}")
            reply_text = ""

        return reply_text

    async def generate_snarky_comment(self) -> str:
        """
        Generates a snarky comment to be used when a user tries to
        use a command that does not exist.
        """
        return random.choice(SNARKY_COMMENTS)
