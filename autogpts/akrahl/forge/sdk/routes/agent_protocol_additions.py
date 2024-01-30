import json
from fastapi import Request, Response
from forge.sdk.errors import NotFoundError
from forge.sdk.forge_log import ForgeLogger
from forge.sdk.model import Step
from .agent_protocol import base_router

LOG = ForgeLogger(__name__)

@base_router.post("/agent/tasks/{task_id}/steps/{step_id}", tags=["agent"], response_model=Step)
async def execute_step(request: Request, task_id: str, step_id: str) -> Response:
    agent = request["agent"]
    try:

        step = await agent.execute_step(task_id, step_id)
        return Response(
            content=step.json(),
            status_code=200,
            media_type="application/json",
        )
    except NotFoundError:
        LOG.exception(f"Error whilst trying to execute a task step: {task_id}")
        return Response(
            content=json.dumps({"error": f"Task not found {task_id}"}),
            status_code=404,
            media_type="application/json",
        )
    except Exception as e:
        LOG.exception(f"Error whilst trying to execute a task step: {task_id}")
        return Response(
            content=json.dumps({"error": "Internal server error"}),
            status_code=500,
            media_type="application/json",
        )