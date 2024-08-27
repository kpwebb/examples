"""
App module to start the chatbot application
"""

import logging
from typing import List, Union

import restate

from chatbot.chat import chatbot
from chatbot.event_deduplicator import event_deduplicator
from chatbot.slackbot import slackbot
from chatbot.taskmanager import workflow_invoker
from chatbot.tasks.flight_prices import flight_watcher
from chatbot.tasks.reminder import reminder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

#
# Add all the services that the chatbot application needs
#
services: List[Union[restate.Workflow | restate.Service | restate.VirtualObject]] = []

services.append(chatbot)
services.append(workflow_invoker)
services.append(reminder)
services.append(flight_watcher)

if slackbot:
    services.append(slackbot)
    services.append(event_deduplicator)

app = restate.app(services)
