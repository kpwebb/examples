import uuid
from typing import Callable, Dict, TypeVar, Generic, Any, Awaitable, TypedDict
from dataclasses import dataclass, field
from uuid import UUID

from restate import Context, WorkflowContext, WorkflowSharedContext, Service, Workflow

from chatbot import chat
from chatbot.utils.types import TaskResult

# ----------------------------------------------------------------------------
#  The Task Manager has the map of available task workflows.
#  It maintains the mapping from task_type (name of the task type) to the
#  implementing workflow service, and has the utilities to start, cancel,
#  and query them.
# ----------------------------------------------------------------------------

# ------------------ defining new types of task workflows --------------------

P = TypeVar('P')


class TaskWorkflow(Generic[P]):
    async def run(self, ctx: WorkflowContext, params: P) -> str:
        pass

    async def cancel(self, ctx: WorkflowSharedContext) -> None:
        pass

    async def current_status(self, ctx: WorkflowSharedContext) -> Any:
        pass


@dataclass
class TaskSpec(Generic[P]):
    task_type_name: str
    task_workflow: Workflow
    params_parser: Callable[[str, dict], P]


available_task_types: Dict[str, TaskSpec] = {}


def register_task_workflow(task: TaskSpec) -> None:
    available_task_types[task.task_type_name] = task


# ----------------- start / cancel / query task workflows --------------------

@dataclass
class TaskOpts:
    name: str
    workflow_name: str
    params: dict

async def start_task(ctx: Context, channel_for_result: str, task_opts: TaskOpts) -> UUID:
    task = available_task_types.get(task_opts.workflow_name)
    if not task:
        raise ValueError(f"Unknown task type: {task_opts.workflow_name}")

    workflow_params = task.params_parser(task_opts.name, task_opts.params)
    workflow_id = await ctx.run("workflow_id", lambda: str(uuid.uuid4()))

    ctx.service_send(invoke_workflow, {
        'task_name': task_opts.name,
        'workflow_service_name': task.task_workflow.__class__.__name__,
        'workflow_params': workflow_params,
        'workflow_id': workflow_id,
        'channel_for_result': channel_for_result
    })

    return workflow_id


async def cancel_task(ctx: Context, workflow_name: str, workflow_id: str) -> None:
    task = available_task_types.get(workflow_name)
    if not task:
        raise ValueError(f"Unknown task type: {workflow_name}")

    await ctx.workflow_call(task.task_workflow.cancel, workflow_id, None)


async def get_task_status(ctx: Context, workflow_name: str, workflow_id: str) -> Any:
    task = available_task_types.get(workflow_name)
    if not task:
        raise ValueError(f"Unknown task type: {workflow_name}")

    return await ctx.workflow_call(task.task_workflow.current_status, workflow_id, None)


workflow_invoker = Service("workflowInvoker")

@workflow_invoker.handler()
async def invoke_workflow(ctx: Context, opts: dict) -> None:
    task_workflow_api = TaskWorkflow[str]()
    response: TaskResult
    try:
        result = await ctx.workflow_call(task_workflow_api.run, opts['workflow_id'], opts['workflow_params'])
        response = TaskResult(task_name=opts['task_name'], result=result)
    except Exception as e:
        response = TaskResult(task_name=opts['task_name'], result=f"Task failed: {str(e)}")

    ctx.object_send(chat.task_done, opts['channel_for_result'], response)