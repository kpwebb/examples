"""
VirtualObject for chatbot, which manages the chat history and ongoing tasks.
"""

from typing import Dict
import typing

from restate import VirtualObject, ObjectContext

from chatbot.utils import gpt
from chatbot.utils.gpt import async_task_notification, ChatEntry
from chatbot.utils.prompt import setup_prompt, tasks_to_prompt, parse_gpt_response
from chatbot.utils.prompt import interpret_command, RunningTask
from chatbot.utils.types import TaskResult

chatbot = VirtualObject("chatSession")

@chatbot.handler()
async def chat_message(ctx: ObjectContext, message: str):
    """
    Manage the chat history and ongoing tasks, and call the GPT model to generate a response.
    """
    # get current history and ongoing tasks
    chat_history: list[ChatEntry] = await ctx.get("chat_history") or []
    active_tasks: Dict[str, RunningTask] = await ctx.get("tasks") or {}

    async def chat():
        return await gpt.chat(
            setup_prompt(),
            chat_history,
            [tasks_to_prompt(active_tasks), message]
        )

    # call LLM and parse response
    gpt_response = await ctx.run("call GPT", chat)

    command = parse_gpt_response(gpt_response["response"])

    # interpret the command and fork tasks as indicated
    output = await interpret_command(ctx, ctx.key(), active_tasks, command)

    # persist the new active tasks and updated history
    if output["newActiveTasks"]:
        ctx.set("tasks", output["newActiveTasks"])

    new_history = gpt.concat_history(chat_history,
                                     {"user": message, "bot": gpt_response["response"]})
    ctx.set("chat_history", new_history)

    return {
        "message": command.message,
        "quote": output["taskMessage"]
    }


@chatbot.handler()
async def task_done(ctx: ObjectContext, result: TaskResult):
    """
    Handle the completion of a task and notify the user.
    """
    task_name = result["task_name"]
    task_result = result["result"]

    # Remove task from list of active tasks
    active_tasks: Dict[str, RunningTask] = await ctx.get("tasks") or {}
    if task_name in active_tasks:
        active_tasks.pop(task_name)
    ctx.set("tasks", active_tasks)

    history: typing.List[ChatEntry] | None = await ctx.get("chat_history")
    new_history = gpt.concat_history(history=history,
                                     entries={"user": f"The task with name '{task_name}' is finished.",
                                              "bot": None})
    ctx.set("chat_history", new_history)

    async_task_notification(session=ctx.key(),
                            msg=f"Task {task_name} says: {task_result}")
