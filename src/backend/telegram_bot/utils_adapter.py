"""
Utility functions for Telegram Bot
"""
import structlog
from telegram import Update

logger = structlog.get_logger()


def escape_markdown(text: str) -> str:
    """
    Escape special Markdown characters for Telegram.
    This prevents parsing errors when text contains unbalanced markers.
    """
    # Characters that need escaping in Markdown mode
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    result = text
    for char in escape_chars:
        result = result.replace(char, '\\' + char)
    
    return result


def sanitize_markdown(text: str) -> str:
    """
    Try to fix common Markdown issues that cause Telegram parsing errors.
    Removes unbalanced asterisks and underscores.
    """
    # Count asterisks and underscores - if odd, remove formatting
    if text.count('*') % 2 != 0:
        text = text.replace('*', '')
    if text.count('_') % 2 != 0:
        text = text.replace('_', '')
    if text.count('`') % 2 != 0:
        text = text.replace('`', '')
    
    return text


async def send_text_safe(update: Update, text: str):
    """
    Send text with fallback to plain text if Markdown fails.
    """
    try:
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as parse_error:
        logger.warning("markdown_parse_failed", error=str(parse_error))
        # Fallback: send without Markdown formatting
        await update.message.reply_text(text)
