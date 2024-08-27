import os

from restate import Service, Context

import logging

from chatbot.chat import chat_message
from chatbot.event_deduplicator import is_new_message
from chatbot.utils import slackutils as slack

logging.basicConfig(level=logging.DEBUG)

SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# ----------------------------------------------------------------------------
#  The slack bot adapter
#
#  This is a proxy between slack webhooks/APIs and the chatbot, dealing
#  with all slack specific things, like deduplication, errors, formatting,
#  message updates, showing the bot's busy status, etc.
# ----------------------------------------------------------------------------
slackbot = Service("slackbot")


# This is the handler hit by the webhook. We do minimal stuff here to
# acknowledge the webhook as soon as possible (since it is guaranteed
# to be durable in Restate).
@slackbot.handler()
async def message(ctx: Context, msg: slack.SlackMessage):
    # verify first that event is legit
    slack.verify_signature(ctx.request().body, ctx.request().headers, SLACK_SIGNING_SECRET)

    # handle challenges - part of Slack's endpoint verification
    if msg["type"] == "url_verification":
        return {"challenge": msg["challenge"]}

    # ignore messages like updates and echos from the bot itself
    if slack.filter_irrelevant_messages(msg, SLACK_BOT_USER_ID):
        return

    # run actual message processing asynchronously
    ctx.service_send(process, arg=msg)

    return


# This does the actual message processing, including de-duplication,
# interacting with status updates, and interacting with the chatbot.
@slackbot.handler()
async def process(ctx: Context, msg: slack.SlackMessage):
    channel = msg["event"]["channel"]
    text = msg["event"]["text"]

    # deduplicate messages
    is_new_msg = await ctx.object_call(is_new_message, key=channel, arg=msg["event_id"])

    if not is_new_msg:
        return

    # send a 'typing...' message to slack
    processing_msg_timestamp = await ctx.run("processing_msg_timestamp",
                                             lambda: slack.send_processing_message(channel, text))

    # talk to the chatbot - with a Virtual Object per channel
    try:
        response = await ctx.object_call(chat_message, key=channel, arg=text)
    except Exception as e:
        error_msg = f"Failed to process: {text}"
        await ctx.run("post error reply", lambda: slack.send_error_message(
            channel, error_msg, str(e), processing_msg_timestamp))
        return

    # the reply replaces the "typing..." message
    await ctx.run("post reply", lambda: slack.send_result_message(
        channel, response["message"], response["quote"], processing_msg_timestamp))
