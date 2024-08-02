from dataclasses import dataclass
from typing import TypeVar, Generic, Any, Callable, Dict, Awaitable

from restate import WorkflowContext, WorkflowSharedContext, Workflow

# ------------------ defining new types of task workflows --------------------

P = TypeVar('P')


class TaskWorkflow(Generic[P]):
    def __init__(self, run: Callable[[WorkflowContext, P], Awaitable[str]],
                 cancel: Callable[[WorkflowSharedContext], Awaitable[None]],
                 current_status: Callable[[WorkflowSharedContext], Awaitable[Any]]):
        self.run = run
        self.cancel = cancel
        self.current_status = current_status

    async def run(self, ctx: WorkflowContext, params: P) -> str:
        return await self.run(ctx, params)

    async def cancel(self, ctx: WorkflowSharedContext) -> None:
        await self.cancel(ctx)

    async def current_status(self, ctx: WorkflowSharedContext) -> Any:
        return await self.current_status(ctx)


@dataclass
class TaskSpec(Generic[P]):
    task_type_name: str
    task_workflow: TaskWorkflow[P]
    params_parser: Callable[[str, dict], P]
