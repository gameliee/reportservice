from datetime import datetime
from logging import Logger
import httpx

from ...settings import AppSettingsModel


async def render_and_send_today(content_id: str, settings: AppSettingsModel, timeout=60, logger: Logger = None):
    params = {"render_date": datetime.now()}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"http://localhost:{settings.PORT}/content/{content_id}/render_and_send", params=params, timeout=timeout
        )

    return r
