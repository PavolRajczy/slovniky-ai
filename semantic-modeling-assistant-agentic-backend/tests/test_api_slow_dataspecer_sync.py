"""A slow Dataspecer update never holds up the rest of the backend."""
import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from fastapi import FastAPI

from api.controllers.design_project_controller import router

app = FastAPI()
app.include_router(router)

PROJECT_ID = "project-1"
CONTROLLER = "api.controllers.design_project_controller"


@patch(f"{CONTROLLER}.activity_service")
@patch(f"{CONTROLLER}.design_project_service")
def test_a_slow_dataspecer_sync_does_not_block_other_requests(project_service, activity_service):
    project_service.load_project.return_value = SimpleNamespace(id=PROJECT_ID)
    dataspecer_answered = threading.Event()

    def wait_for_dataspecer(project_id):
        dataspecer_answered.wait(timeout=5)
        return True

    project_service.push_ontology_to_dataspecer.side_effect = wait_for_dataspecer

    async def sync_while_polling():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as http:
            syncing = asyncio.create_task(http.post(f"/projects/{PROJECT_ID}/dataspecer-sync"))
            await asyncio.sleep(0.2)
            polling = await asyncio.wait_for(http.get(f"/projects/{PROJECT_ID}/knowledge-base/jobs/unknown-job"), timeout=2)
            sync_was_pending = not syncing.done()
            dataspecer_answered.set()
            return polling.status_code, sync_was_pending, (await syncing).status_code

    assert asyncio.run(sync_while_polling()) == (404, True, 200)
