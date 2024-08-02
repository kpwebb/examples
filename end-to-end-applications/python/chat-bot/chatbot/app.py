import logging

import restate

from chatbot.chat import chatbot
from chatbot.slackbot import slackbot
from chatbot.taskmanager import workflow_invoker
import chatbot.taskmanager as tm
from chatbot.tasks.flight_prices import flightTask, flight_watcher
from chatbot.tasks.reminder import reminderTask, reminder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

tm.register_task_workflow(reminderTask)
tm.register_task_workflow(flightTask)

app = restate.app(services=[chatbot, slackbot, workflow_invoker, reminder, flight_watcher])
