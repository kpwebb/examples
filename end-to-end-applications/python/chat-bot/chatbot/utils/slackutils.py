import os

from restate.exceptions import TerminalError
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier

from typing import TypedDict, Optional, Sequence


class Event(TypedDict):
    text: str
    channel: str
    user: str


class SlackMessage(TypedDict):
    type: str
    event: Event
    event_id: str
    challenge: Optional[str]


SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

if not (SLACK_BOT_USER_ID and SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET):
    print("Missing some SlackBot env variables (SLACK_BOT_USER_ID, SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET)")
    exit(1)

slack_client = WebClient()


def filter_irrelevant_messages(msg: SlackMessage, slack_bot_user: str) -> bool:
    # ignore anything that is not an event callback
    if msg["type"] != "event_callback" or not msg.get("event"):
        return True

    # ignore messages from ourselves
    if msg["event"].get("user") == slack_bot_user:
        return True

    # ignore messages that are not raw but updates
    if msg["event"].get("user") is None or msg["event"].get("text") is None:
        return True

    return False


def verify_signature(body, headers, signing_secret):
    request_signature = headers.get("x-slack-signature")
    ts_header = headers.get("x-slack-request-timestamp")

    if not request_signature:
        raise TerminalError("Header 'x-slack-signature' missing", status_code=400)
    if not ts_header:
        raise TerminalError("Header 'x-slack-request-timestamp' missing", status_code=400)

    try:
        request_timestamp = int(ts_header)
    except ValueError:
        raise TerminalError(f"Cannot parse header 'x-slack-request-timestamp': {ts_header}", status_code=400)

    try:
        verifier = SignatureVerifier(signing_secret)
        verifier.is_valid_request(
            body=body.decode("utf-8"),
            headers={
                "x-slack-signature": request_signature,
                "x-slack-request-timestamp": request_timestamp
            }
        )
    except Exception as e:
        raise TerminalError("Event signature verification failed", status_code=400)


def send_processing_message(channel: str, text: str):
    blocks = [{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":typing:"
        }
    }]
    return post_to_slack(channel=channel, text=text, blocks=blocks)


def post_to_slack(channel: str, text: str, blocks: Sequence[dict]):
    slack_response = slack_client.chat_postMessage(channel=channel, text=text, blocks=blocks)

    if not slack_response["ok"] or slack_response["error"]:
        raise Exception(f"Failed to send message to slack: {slack_response['error']}")

    if not slack_response["ts"]:
        raise Exception(f"Missing message timestamp in response: {slack_response}")

    return slack_response["ts"]


def send_result_message(channel: str, text: str, quote: str | None, msgTimestamp: str):
    blocks = [{
        "type": "section",
        "text": {
            "type": "plain_text",
            "text": text
        }
    }]

    if quote:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": make_markdown_quote(quote)
            }
        })

    return update_message_in_slack(channel=channel, text=text, blocks=blocks)


def send_error_message(channel: str, error_msg: str, quote: str | None, replace_msg_timestamp: str | None):
    blocks = [
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":exclamation: :exclamation: {error_msg}"
            }
        }
    ]

    if quote:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": make_markdown_quote(quote)
            }
        })

    blocks.append({"type": "divider"})

    return update_message_in_slack(
        channel=channel, text=error_msg, blocks=blocks, replace_msg_timestamp=replace_msg_timestamp)


def make_markdown_quote(text: str) -> str:
    lines = text.split("\n")
    return ":memo: " + " \n> ".join(lines)


def update_message_in_slack(channel: str, text: str, blocks: Sequence[dict], replace_msg_timestamp: str | None):
    if replace_msg_timestamp:
        slack_client.chat_update(
            channel=channel, text=text, blocks=blocks, ts=replace_msg_timestamp)
    else:
        slack_client.chat_postMessage(channel=channel, text=text, blocks=blocks)


def notification_handler(channel: str, message: str):
    blocks = [
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":speech_balloon: {message}"
            }
        },
        {
            "type": "divider"
        }
    ]

    return post_to_slack(channel=channel, text=message, blocks=blocks)
