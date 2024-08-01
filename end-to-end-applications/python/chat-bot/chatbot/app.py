import restate

from chatbot.chat import chatbot
from chatbot.slackbot import slackbot
from chatbot.taskmanager import workflow_invoker

app = restate.app(services=[chatbot, slackbot, workflow_invoker])
