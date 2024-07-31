import restate

from chatbot.chat import chatbot
from chatbot.slackbot import slackbot
from chatbot.taskmanager import taskmanager

app = restate.app(services=[chatbot, slackbot, taskmanager])
