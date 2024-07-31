from restate import VirtualObject

slackbot = VirtualObject("slackbot")


@slackbot.handler()
async def hello():
    return
