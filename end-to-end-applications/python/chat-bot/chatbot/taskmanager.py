from restate import VirtualObject

taskmanager = VirtualObject("taskManager")


@taskmanager.handler()
async def chat_message():
    return
