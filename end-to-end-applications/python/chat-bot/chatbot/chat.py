from dataclasses import dataclass
from typing import Dict

from restate import VirtualObject, ObjectContext

from chatbot.utils import gpt
from chatbot.utils.gpt import async_task_notification
from chatbot.utils.prompt import setup_prompt, tasks_to_prompt, parse_gpt_response, interpret_command, RunningTask


@dataclass
class TaskResult:
    task_name: str
    result: str


chatbot = VirtualObject("chatSession")


@chatbot.handler()
async def chat_message(ctx: ObjectContext, message: str):
    # get current history and ongoing tasks
    chat_history = await ctx.get("chat_history") or []
    active_tasks = await ctx.get("tasks") or []

    async def chat():
        return await gpt.chat(
            setup_prompt(),
            chat_history,
            [tasks_to_prompt(active_tasks), message]
        )

    # call LLM and parse response
    gpt_response = await ctx.run("call GPT", chat)

    command = parse_gpt_response(gpt_response['response'])

    # interpret the command and fork tasks as indicated
    new_active_tasks, task_message = await interpret_command(ctx, ctx.key(), active_tasks, command)

    # persist the new active tasks and updated history
    if new_active_tasks:
        ctx.set("tasks", new_active_tasks)
    ctx.set("chat_history", gpt.concat_history(chat_history, {"user": message, "bot": gpt_response['response']}))

    return {
        "message": command['message'],
        "quote": task_message
    }


@chatbot.handler()
async def task_done(ctx: ObjectContext, result: TaskResult):
    # Remove task from list of active tasks
    active_tasks: Dict[str, RunningTask] = await ctx.get("tasks") or {}
    if result.task_name in active_tasks:
        active_tasks.pop(result.task_name)
    ctx.set("tasks", active_tasks)

    history = await ctx.get("chat_history")
    new_history = gpt.concat_history(history=history, entries={"user": f"The task with name '{result.task_name}' is finished."})
    ctx.set("chat_history", new_history)

    return await async_task_notification(ctx, ctx.key(), f"Task {result.task_name} says: {result.result}")
