import logging

import restate

from chatbot.chat import chatbot
from chatbot.event_deduplicator import event_deduplicator
from chatbot.slackbot import slackbot
from chatbot.taskmanager import workflow_invoker
import chatbot.taskmanager as tm
from chatbot.tasks.flight_prices import flightTask, flight_watcher
from chatbot.tasks.reminder import reminderTask, reminder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# (1) register the task types we have at the task manager
#     so that the task manager knows where to send certain commands to
tm.register_task_workflow(reminderTask)
tm.register_task_workflow(flightTask)

#  (2) build the endpoint with the core handlers for the chat
services = [chatbot, workflow_invoker, reminder, flight_watcher]

#  (3) add slackbot if in slack mode
if slackbot:
    services.append(slackbot)
    services.append(event_deduplicator)


app = restate.app(services)