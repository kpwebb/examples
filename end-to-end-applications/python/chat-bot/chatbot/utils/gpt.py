import asyncio
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
import requests

from typing import List, Dict, Union, Optional, Callable

from restate import ObjectContext
from restate.serde import Serde

from chatbot.slackbot import slackbot

# ----------------------------------------------------------------------------
#  Utilities and helpers to interact with OpenAI GPT APIs.
# ----------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("Missing OPENAI_API_KEY environment variable")
    exit(1)

OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o"
TEMPERATURE = 0.2  # use more stable (less random / creative) responses

MODE = os.environ.get("MODE", "CONSOLE")


class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

    def to_json(self):
        return self.value


@dataclass
class ChatEntry:
    role: Role
    content: str

    def to_json(self):
        return {
            "role": self.role.to_json(),
            "content": self.content
        }


@dataclass
class GptResponse:
    response: str
    tokens: int


class GptResponseSerde(Serde[GptResponse]):
    def deserialize(self, buf: bytes) -> Optional[GptResponse]:
        if not buf:
            return None
        data = json.loads(buf)
        return GptResponse(response=data["response"], tokens=data["tokens"])

    def serialize(self, obj: Optional[GptResponse]) -> bytes:
        if obj is None:
            return bytes()
        data = {
            "response": obj.response,
            "tokens": obj.tokens
        }
        return bytes(json.dumps(data), "utf-8")


def check_rethrow_terminal_error(error):
    # Implement your error handling logic here
    raise error


def http_response_to_error(status, text):
    # Implement your HTTP error handling logic here
    raise Exception(f"HTTP Error {status}: {text}")


async def chat(setup_prompt: str, history: List[ChatEntry], user_prompts: List[str]) -> GptResponse:
    setup_prompt = [ChatEntry(role=Role.SYSTEM, content=setup_prompt)]
    user_prompts = [ChatEntry(role=Role.USER, content=user_prompt) for user_prompt in user_prompts]
    full_prompt: List[ChatEntry] = setup_prompt + history + user_prompts

    response = await call_gpt(full_prompt)

    return GptResponse(response=response["message"]["content"], tokens=response["total_tokens"])


async def call_gpt(messages: List[ChatEntry]) -> Dict[str, Union[ChatEntry, int]]:
    try:
        body = {
            "model": MODEL,
            "temperature": TEMPERATURE,
            "messages": [m.to_json() for m in messages]
        }

        response = requests.post(
            OPENAI_ENDPOINT,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=body
        )

        if not response.ok:
            http_response_to_error(response.status_code, response.text)

        data = response.json()
        message = data["choices"][0]["message"]
        total_tokens = data["usage"]["total_tokens"]
        return {"message": message, "total_tokens": total_tokens}

    except Exception as error:
        logging.error(f"Error calling model {MODEL} at {OPENAI_ENDPOINT}: {error}")
        check_rethrow_terminal_error(error)


def concat_history(history: List[ChatEntry], entries: Dict[str, Optional[str]]):
    chat_history = history or []
    new_entries = [ChatEntry(role=Role.USER, content=entries["user"])]

    if entries.get("bot"):
        new_entries.append({"role": Role.ASSISTANT, "content": entries["bot"]})


async def async_task_notification(ctx: ObjectContext, session: str, msg: str):
    if MODE == "SLACK":
        await slackbot.notificationHandler()

    logging.info(f" --- NOTIFICATION from session {session} --- : {msg}")
