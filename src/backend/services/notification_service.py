"""
Notification service for Telegram messages
"""
import asyncio
import aiohttp
from typing import Dict, Optional

from backend.config import config


class NotificationService:
    """
    Service for sending notifications via Telegram
    """
    
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_telegram_message(
        self,
        chat_id: int,
        message: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
        reply_markup: Optional[Dict] = None
    ) -> Dict:
        """
        Send message to Telegram chat
        
        Args:
            chat_id: Telegram chat ID
            message: Message text
            parse_mode: Message parse mode (HTML, Markdown)
            disable_notification: Silent notification
            reply_markup: Inline keyboard markup
            
        Returns:
            Telegram API response
        """
        print(f"📤 Sending Telegram message to chat {chat_id}")
        
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                
                if result.get("ok"):
                    print(f"✅ Message sent successfully")
                else:
                    print(f"❌ Error sending message: {result}")
                
                return result
    
    async def notify_download_complete(
        self,
        chat_id: int,
        bill_number: str,
        documents_count: int
    ):
        """Notify user that bill download is complete"""
        message = (
            f"✅ <b>Завантаження завершено!</b>\n\n"
            f"📄 Законопроєкт #{bill_number}\n"
            f"📎 Завантажено {documents_count} документів\n\n"
            f"🔍 Готовий до аналізу!\n"
            f"/analyze_{bill_number} - розпочати аналіз"
        )
        
        await self.send_telegram_message(chat_id, message)
    
    async def notify_analysis_complete(
        self,
        chat_id: int,
        bill_number: str,
        analysis_id: str
    ):
        """Notify user that analysis is complete"""
        message = (
            f"✅ <b>Аналіз завершено!</b>\n\n"
            f"📄 Законопроєкт #{bill_number}\n"
            f"🤖 AI аналіз готовий\n\n"
            f"Переглянути результати: /result_{analysis_id}"
        )
        
        await self.send_telegram_message(chat_id, message)
    
    async def notify_error(
        self,
        chat_id: int,
        error_message: str
    ):
        """Notify user about error"""
        message = (
            f"❌ <b>Помилка</b>\n\n"
            f"{error_message}\n\n"
            f"Спробуйте ще раз або зверніться до адміністратора."
        )
        
        await self.send_telegram_message(chat_id, message)
