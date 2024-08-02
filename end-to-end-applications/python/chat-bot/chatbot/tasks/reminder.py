import time
from datetime import datetime, timedelta
from typing import TypedDict, Any

from restate import Workflow, WorkflowContext, WorkflowSharedContext
from restate.exceptions import TerminalError

from chatbot.tasks.task_workflow import TaskWorkflow, TaskSpec

reminder = Workflow("reminder")


class ReminderOpts(TypedDict):
    timestamp: int
    description: str


@reminder.main()
async def run(ctx: WorkflowContext, opts: ReminderOpts):
    print(f"Reminder: {opts}")
    ctx.set("timestamp", opts["timestamp"])
    time_now = await ctx.run("time", lambda: round(time.time() * 1000))

    delay = opts["timestamp"] - time_now

    if delay < 0:
        raise TerminalError("Can't set a reminder in the past")

    await ctx.sleep(timedelta(milliseconds=delay))

    # Replace this by ctx.race, once the SDK supports promise combinators
    cancelled = await ctx.promise("cancelled").peek()
    if cancelled:
        return "The reminder has been cancelled"

    return f"It is time{opts.get('description', '!')}"


@reminder.handler()
async def cancel(ctx: WorkflowSharedContext):
    await ctx.promise("cancelled").resolve(True)


@reminder.handler()
async def current_status(ctx: WorkflowSharedContext) -> dict:
    timestamp = await ctx.get("timestamp")
    if not timestamp:
        return {"remainingTime": -1}

    current_time = ctx.run("time", lambda: round(time.time() * 1000))
    time_remaining = timestamp - current_time
    return {"remainingTime": time_remaining if time_remaining > 0 else 0}


def params_parser(name: str, params: Any) -> ReminderOpts:
    date_string = params.get("date")
    if not isinstance(date_string, str):
        raise ValueError("Missing string field 'date' in parameters for task type 'reminder'")

    date = datetime.fromisoformat(date_string)
    timestamp = int(date.timestamp() * 1000)

    description = params.get("description")
    if not isinstance(description, str):
        description = None

    return ReminderOpts(timestamp=timestamp, description=description)


reminderTask = TaskSpec(
    params_parser=params_parser,
    task_type_name="reminder",
    task_workflow=TaskWorkflow(
        run=run,
        cancel=cancel,
        current_status=current_status
    )
)
