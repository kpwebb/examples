from restate.object import VirtualObject
from restate.context import ObjectContext

from example.chatbot.utils import gpt
from example.chatbot.utils.prompt import setup_prompt, tasks_to_prompt

chatbot = VirtualObject("chatSession")


@chatbot.handler()
async def chat_message(ctx: ObjectContext, message: str):

    # get current history and ongoing tasks
    chat_history = await ctx.get("chat_history")
    active_tasks = await ctx.get("tasks")

    # call LLM and parse response
    gpt_response = ctx.run("call GTP", lambda: gpt.chat(
        setup_prompt(),
        chat_history,
        [tasks_to_prompt(active_tasks), message]
    ))

    command = parse_gpt_response(gpt_response.response)


    new_active_tasks = interpret_command(ctx, ctx.key(), active_tasks, command)





