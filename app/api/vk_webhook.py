from fastapi import APIRouter, Request, Response

from app.config import settings
from app.services.vk_service import handle_vk_event

router = APIRouter()


@router.post("/api/vk/callback")
async def vk_callback(request: Request):
    data = await request.json()
    event_type = data.get("type")

    if event_type == "confirmation":
        return Response(content=settings.vk_confirmation_code, media_type="text/plain")

    secret = data.get("secret")
    if secret and secret != settings.vk_secret_key:
        return Response(content="forbidden", status_code=403)

    await handle_vk_event(data)
    return Response(content="ok", media_type="text/plain")
