import json

from fastapi import APIRouter, Request, Response

from app.services.payment_service import handle_payment_notification

router = APIRouter()


@router.post("/api/payment/webhook")
async def yokassa_webhook(request: Request):
    body = await request.body()
    data = json.loads(body)
    await handle_payment_notification(data)
    return Response(status_code=200)
