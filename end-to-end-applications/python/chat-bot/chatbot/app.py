import restate

from chatbot.chat import chatbot
from chatbot.slackbot import slackbot
from chatbot.taskmanager import workflow_invoker
import taskmanager as tm
from chatbot.tasks.reminder import reminderTask, reminder

tm.register_task_workflow(reminderTask)

app = restate.app(services=[chatbot, slackbot, workflow_invoker, reminder])
