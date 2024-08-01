from datetime import datetime
from typing import TypedDict

from restate import Workflow, WorkflowContext, WorkflowSharedContext

reminder = Workflow("reminder")


class ReminderOpts(TypedDict):
    timestamp: datetime
    description: str


@reminder.handlers()
async def run(ctx: WorkflowContext, opts: ReminderOpts):
    ctx.set("timestamp", opts["timestamp"])
    time_now = await ctx.run("time", lambda: datetime.now())

    delay = opts["timestamp"] - time_now

    await ctx.sleep(delay)

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

    current_time = int(datetime.now() * 1000)
    time_remaining = timestamp - current_time
    return {"remainingTime": time_remaining if time_remaining > 0 else 0}
