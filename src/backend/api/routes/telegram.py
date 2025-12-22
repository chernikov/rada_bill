"""
Telegram Bot API endpoints
"""
import structlog
from fastapi import APIRouter, Request, HTTPException, Header, Body
from typing import Optional

from backend.config import config
from backend.telegram_bot.bot import bot

logger = structlog.get_logger()

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None)
):
    """
    Webhook endpoint для входящих повідомлень від Telegram.
    
    Telegram надсилає Updates на цей endpoint.
    """
    # Verify secret token (commented out for now - Telegram sends different token)
    # if config.TELEGRAM_SECRET_TOKEN and x_telegram_bot_api_secret_token != config.TELEGRAM_SECRET_TOKEN:
    #     logger.warning(
    #         "webhook_unauthorized",
    #         provided_token=x_telegram_bot_api_secret_token[:10] if x_telegram_bot_api_secret_token else None
    #     )
    #     raise HTTPException(status_code=403, detail="Invalid secret token")
    
    try:
        update_data = await request.json()
        logger.info("webhook_received", update_id=update_data.get('update_id'))
        
        # Process update with bot handlers
        await bot.process_update(update_data)
        
        return {"ok": True}
    
    except Exception as e:
        logger.error("webhook_processing_failed", error=str(e))
        # Still return 200 to Telegram to avoid retries
        return {"ok": False, "error": str(e)}


@router.post("/setup-webhook")
async def setup_webhook():
    """
    Налаштувати вебхук для Telegram боту.
    
    Викликається один раз після деплою для налаштування вебхука.
    """
    if not config.TELEGRAM_WEBHOOK_URL:
        raise HTTPException(
            status_code=400,
            detail="TELEGRAM_WEBHOOK_URL not configured"
        )
    
    if not config.TELEGRAM_SECRET_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="TELEGRAM_SECRET_TOKEN not configured"
        )
    
    try:
        success = await bot.set_webhook(
            webhook_url=config.TELEGRAM_WEBHOOK_URL,
            secret_token=config.TELEGRAM_SECRET_TOKEN
        )
        
        if success:
            return {
                "ok": True,
                "message": "Webhook налаштовано успішно",
                "webhook_url": config.TELEGRAM_WEBHOOK_URL
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to set webhook"
            )
    
    except Exception as e:
        logger.error("setup_webhook_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Setup webhook error: {str(e)}"
        )


@router.post("/delete-webhook")
async def delete_webhook():
    """
    Видалити вебхук (для переключення на polling mode).
    """
    try:
        success = await bot.delete_webhook()
        
        return {
            "ok": True,
            "message": "Webhook видалено",
            "success": success
        }
    
    except Exception as e:
        logger.error("delete_webhook_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Delete webhook error: {str(e)}"
        )


@router.get("/webhook-info")
async def get_webhook_info():
    """
    Отримати інформацію про поточний вебхук.
    """
    try:
        info = await bot.get_webhook_info()
        
        return {
            "ok": True,
            "webhook_info": info
        }
    
    except Exception as e:
        logger.error("webhook_info_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Get webhook info error: {str(e)}"
        )


@router.post("/send")
async def send_message(message_data: dict = Body(...)):
    """
    Надіслати повідомлення користувачу через бота.
    
    Body:
    {
        "chat_id": 12345,
        "text": "Hello, user!",
        "parse_mode": "Markdown"  # optional
    }
    """
    chat_id = message_data.get("chat_id")
    text = message_data.get("text")
    parse_mode = message_data.get("parse_mode")
    
    if not chat_id or not text:
        raise HTTPException(
            status_code=400,
            detail="chat_id and text are required"
        )
    
    try:
        message = await bot.application.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )
        
        return {
            "ok": True,
            "result": {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "date": message.date.isoformat()
            }
        }
    
    except Exception as e:
        logger.error("send_message_failed", error=str(e), chat_id=chat_id)
        raise HTTPException(
            status_code=500,
            detail=f"Send message error: {str(e)}"
        )


@router.post("/notify")
async def send_notification(notification_data: dict = Body(...)):
    """
    Надіслати notification користувачам.
    
    Body:
    {
        "user_ids": [12345, 67890],
        "message": "New bill analyzed!"
    }
    """
    user_ids = notification_data.get("user_ids", [])
    message = notification_data.get("message", "")
    
    if not user_ids or not message:
        raise HTTPException(
            status_code=400,
            detail="user_ids and message are required"
        )
    
    try:
        results = []
        
        for user_id in user_ids:
            try:
                msg = await bot.application.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
                results.append({
                    "user_id": user_id,
                    "success": True,
                    "message_id": msg.message_id
                })
            except Exception as e:
                logger.error("notify_user_failed", user_id=user_id, error=str(e))
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "ok": True,
            "results": results,
            "total": len(user_ids),
            "success_count": sum(1 for r in results if r["success"])
        }
    
    except Exception as e:
        logger.error("notification_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Notification error: {str(e)}"
        )
