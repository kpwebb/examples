import os
from enum import Enum

import requests
from typing import List, Dict, Union, Optional, TypedDict

# ----------------------------------------------------------------------------
#  Utilities and helpers to interact with OpenAI GPT APIs.
# ----------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Missing OPENAI_API_KEY environment variable")
    exit(1)

OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o"
TEMPERATURE = 0.2  # use more stable (less random / creative) responses


class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatEntry(TypedDict):
    role: Role
    content: str


class GptResponse(TypedDict):
    response: str
    tokens: int


def check_rethrow_terminal_error(error):
    # Implement your error handling logic here
    raise error


def http_response_to_error(status, text):
    # Implement your HTTP error handling logic here
    raise Exception(f"HTTP Error {status}: {text}")


async def chat(setup_prompt: str, history: List[ChatEntry], user_prompts: List[str]) -> GptResponse:
    setup_prompt = [{"role": "system", "content": setup_prompt}]
    user_prompts = [{"role": "user", "content": user_prompt} for user_prompt in user_prompts]
    full_prompt = setup_prompt + history + user_prompts

    response = await call_gpt(full_prompt)

    return {
        "response": response["message"]["content"],
        "tokens": response["total_tokens"]
    }


async def call_gpt(messages: List[ChatEntry]) -> Dict[str, Union[ChatEntry, int]]:
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
            json=body
        )

        if not response.ok:
            http_response_to_error(response.status_code, response.text)

        data = response.json()
        message = data["choices"][0]["message"]
        total_tokens = data["usage"]["total_tokens"]
        return {"message": message, "total_tokens": total_tokens}
    except Exception as error:
        print(f"Error calling model {MODEL} at {OPENAI_ENDPOINT}: {error}")
        check_rethrow_terminal_error(error)


def concat_history(history: Optional[List[ChatEntry]], entries: Dict[str, Optional[str]]) -> List[ChatEntry]:
    chat_history = history or []
    new_entries: List[ChatEntry] = []

    new_entries.append({"role": "user", "content": entries["user"]})
    if entries.get("bot"):
        new_entries.append({"role": "assistant", "content": entries["bot"]})

    return chat_history + new_entries