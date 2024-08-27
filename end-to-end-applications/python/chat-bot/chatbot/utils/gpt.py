"""
Utility model to talk to OpenAI GPT API.
"""

import logging
import os
import sys
from typing import List, Dict, Literal, TypedDict, Any
import requests

from chatbot.utils import slackutils

# ----------------------------------------------------------------------------
#  Utilities and helpers to interact with OpenAI GPT APIs.
# ----------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("Missing OPENAI_API_KEY environment variable")
    sys.exit(1)

OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o"
TEMPERATURE = 0.2  # use more stable (less random / creative) responses

MODE = os.environ.get("MODE", "CONSOLE")

class ChatEntry(TypedDict):
    """Represents a chat entry."""
    role: Literal["user", "assistant", "system"]
    content: str

class NewChatEntry(TypedDict):
    """Represents a new chat entry."""
    user: str
    bot: str | None

class GptResponse(TypedDict):
    """Represents a response from the GPT model."""
    response: str
    tokens: int

async def chat(setup_prompt: str,
               history: List[ChatEntry],
               user_prompts: List[str]) -> GptResponse:
    """
        Setup the prompt and chat with the model using the given user prompts.
    """
    prompt = [ChatEntry(role="system", content=setup_prompt)]
    prompt.extend(history)
    prompt.extend((ChatEntry(role="user", content=user_prompt) for user_prompt in user_prompts))
    return await call_gpt(prompt)


async def call_gpt(messages: List[ChatEntry]) -> GptResponse:
    """
    Call the model with the given messages and return the response.
    """
    try:
        body = {
            "model": MODEL,
            "temperature": TEMPERATURE,
            "messages": messages
        }

        response = requests.post(
            OPENAI_ENDPOINT,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=body,
            timeout=60, # wait for up to 60 seconds for a response
        )

        if not response.ok:
            raise ValueError(f"{response.status_code} : {response.text}")

        data = response.json()
        message = data["choices"][0]["message"]
        total_tokens = data["usage"]["total_tokens"]
        return GptResponse(response=message["content"], tokens=total_tokens)
    except Exception as error:
        logging.error("Error calling model %s at %s: %s", MODEL, OPENAI_ENDPOINT, error)
        raise error


def concat_history(history: List[ChatEntry] | None,
                   entries:  NewChatEntry) -> List[ChatEntry]:
    """
    Add a new chat entry to the history. 
    """
    new_history = history[:] if history is not None else []
    new_history.append({"role": "user", "content": entries["user"]})
    bot = entries.get("bot", None)
    if bot is not None:
        new_history.append({"role": "assistant", "content": bot})
    return new_history


def async_task_notification(session: str, msg: str):
    """
    Send a notification to the user with the given message.
    """
    if MODE != "SLACK":
        logging.info(" --- NOTIFICATION from session %s --- : %s", session, msg)
        return

    blocks: List[Dict[Any, Any]] = [
        {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":speech_balloon: {msg}"
                }
            },
            {
                "type": "divider"
            }
        ]
    slackutils.post_to_slack(session, msg, blocks)
