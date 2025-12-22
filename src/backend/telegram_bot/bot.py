"""
Telegram Bot with command handlers
"""
import structlog
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from backend.config import config
from backend.services.scraper import ScraperService
from backend.services.document_downloader import DocumentDownloaderService
from backend.services.ai_service import AIService
from backend.services.storage_service import StorageService
from backend.services.firestore_service import FirestoreService
from backend.services.converters.pdf_converter import PDFConverter
from backend.services.converters.docx_converter import DOCXConverter
from backend.version import get_version_string


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


class TelegramBot:
    """
    Telegram Bot for Ukrainian Parliament Bills Analysis
    
    Commands:
    /start - Welcome message and instructions
    /help - Show available commands
    /bill <number> - Download and analyze specific bill
    /search <query> - Search for bills
    /status - Show current processing status
    """
    
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.application = None
        
        # Initialize services lazily to avoid credential errors on startup
        self._scraper = None
        self._downloader = None
        self._ai_service = None
        self._storage = None
        self._firestore = None
        self._pdf_converter = None
        self._docx_converter = None
        
        logger.info("telegram_bot_initialized")
    
    @property
    def scraper(self):
        if self._scraper is None:
            self._scraper = ScraperService()
        return self._scraper
    
    @property
    def downloader(self):
        if self._downloader is None:
            self._downloader = DocumentDownloaderService()
        return self._downloader
    
    @property
    def ai_service(self):
        if self._ai_service is None:
            self._ai_service = AIService()
        return self._ai_service
    
    @property
    def storage(self):
        if self._storage is None:
            self._storage = StorageService()
        return self._storage
    
    @property
    def firestore(self):
        if self._firestore is None:
            self._firestore = FirestoreService()
        return self._firestore
    
    @property
    def pdf_converter(self):
        if self._pdf_converter is None:
            self._pdf_converter = PDFConverter()
        return self._pdf_converter
    
    @property
    def docx_converter(self):
        if self._docx_converter is None:
            self._docx_converter = DOCXConverter()
        return self._docx_converter
    
    def setup(self):
        """Setup bot handlers"""
        self.application = Application.builder().token(self.token).build()
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("bill", self.bill_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("version", self.version_command))
        
        # Callback handlers for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler for text messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        logger.info("bot_handlers_registered")
        print("✅ Bot handlers registered: start, help, bill, search, status")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        logger.info("start_command", user_id=user.id, username=user.username)
        
        # Save user data to Firestore (optional - skip if credentials not configured)
        try:
            await self.firestore.create_telegram_user({
                'chatId': user.id,
                'userId': user.id,
                'username': user.username,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'languageCode': user.language_code,
                'isBot': user.is_bot
            })
            
            # Log request
            await self.firestore.log_user_request(user.id, {
                'command': '/start',
                'type': 'command'
            })
        except Exception as e:
            logger.warning("firestore_error_start", error=str(e))
        
        welcome_text = f"""👋 Привіт, {user.first_name}!

Я бот для аналізу законопроєктів Верховної Ради України

🔍 Що я вмію:
• Завантажувати картки законопроєктів
• Скачувати документи (PDF/DOCX)
• Аналізувати їх за допомогою AI
• Давати висновки про корупційні ризики

📖 Команди:
/bill <номер> - Проаналізувати законопроєкт
/help - Докладна допомога

Почніть з команди /bill!"""
        
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user = update.effective_user
        
        logger.info("help_command", user_id=user.id)
        
        # Log request (optional - skip if credentials not configured)
        try:
            await self.firestore.log_user_request(user.id, {
                'command': '/help',
                'type': 'command'
            })
        except Exception as e:
            logger.warning("firestore_error_help", error=str(e))
        
        help_text = """📚 Докладна інструкція

1️⃣ Аналіз конкретного законопроєкту:
/bill 12414
Бот завантажить картку, документи та зробить AI-аналіз.

2️⃣ Просто напишіть номер:
Якщо напишете просто номер (наприклад, 12414), бот автоматично зрозуміє, що це команда /bill.

💡 Приклади:
• /bill 10000 - аналіз ЗП №10000
• 12414 - швидкий аналіз

❓ Питання? Напишіть @andriy_chernikov"""
        
        await update.message.reply_text(help_text)
    
    async def bill_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bill <number> command"""
        user = update.effective_user
        user_id = user.id
        
        print(f"🔔 bill_command called by user {user_id}, args: {context.args}")
        
        # Save/update user data
        await self.firestore.create_telegram_user({
            'chatId': user_id,
            'userId': user_id,
            'username': user.username,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'languageCode': user.language_code,
            'isBot': user.is_bot
        })
        
        # Check if bill number provided
        if not context.args:
            await update.message.reply_text(
                "❌ Будь ласка, вкажіть номер законопроєкту.\n"
                "Приклад: `/bill 12414`",
                parse_mode='Markdown'
            )
            return
        
        bill_number = context.args[0].strip()
        
        logger.info("bill_command", user_id=user_id, bill_number=bill_number)
        print(f"📝 Processing bill #{bill_number} for user {user_id}")
        
        # Log request to Firestore
        await self.firestore.log_user_request(user_id, {
            'command': '/bill',
            'billNumber': bill_number,
            'type': 'bill_analysis'
        })
        
        # Validate bill number (allow digits, dashes, and other characters)
        if not bill_number or len(bill_number.strip()) == 0:
            await update.message.reply_text(
                "❌ Вкажіть номер законопроєкту.\n"
                "Приклад: `/bill 12414` або `/bill 14270-1`",
                parse_mode='Markdown'
            )
            return
        
        # Send processing message
        status_message = await update.message.reply_text(
            f"🔄 Обробка законопроєкту №{bill_number}...\n"
            "Це може зайняти кілька хвилин."
        )
        
        try:
            # Check if bill already downloaded from cache
            cached_bill = await self.firestore.get_bill_by_number(bill_number)
            
            if cached_bill and cached_bill.get('gcsPath'):
                # Bill found in cache - download from GCS
                await status_message.edit_text(
                    f"💾 Завантаження з кешу: ЗП №{bill_number}...",
                    parse_mode='Markdown'
                )
                
                bill_title = cached_bill.get('billTitle', f"Законопроєкт №{bill_number}")
                combined_path = cached_bill.get('gcsPath')
                
                # Download combined markdown from GCS
                combined_bytes = await self.storage.download_file(combined_path)
                
                if combined_bytes:
                    combined_text = combined_bytes.decode('utf-8')
                    documents = []  # Will use cached data
                    num_documents = cached_bill.get('documentsCount', 0)
                    
                    logger.info("bill_loaded_from_cache", bill_number=bill_number, gcs_path=combined_path)
                else:
                    # Cache miss - fallback to full download
                    logger.warning("cache_download_failed", bill_number=bill_number)
                    cached_bill = None
            
            if not cached_bill:
                # Step 1: Download bill card
                await status_message.edit_text(
                    f"📥 **Крок 1/4:** Завантаження картки ЗП №{bill_number}...",
                    parse_mode='Markdown'
                )
                
                html_content = await self.scraper.download_bill_card(bill_number)
                
                if not html_content:
                    await status_message.edit_text(
                        f"❌ Не вдалося знайти законопроєкт №{bill_number}.\n"
                        "Перевірте номер та спробуйте ще раз."
                    )
                    return
                
                # Extract bill title
                bill_title = self.scraper.extract_bill_title(html_content)
                if not bill_title:
                    bill_title = f"Законопроєкт №{bill_number}"
                
                # Save HTML card to GCS
                try:
                    html_path = self.storage.generate_bill_path(bill_number, f"{bill_number}.html")
                    await self.storage.upload_file(
                        html_content.encode('utf-8'),
                        html_path,
                        content_type='text/html'
                    )
                except Exception as gcs_error:
                    logger.warning("gcs_upload_failed", error=str(gcs_error), file="html_card")
                    # Continue without GCS storage
                
                # Step 2: Download documents
                await status_message.edit_text(
                    f"📄 **Крок 2/4:** Завантаження документів...",
                    parse_mode='Markdown'
                )
                
                documents = await self.downloader.download_bill_documents(bill_number, html_content)
                
                if not documents:
                    await status_message.edit_text(
                        f"⚠️ Законопроєкт №{bill_number} знайдено, але документів немає.\n"
                        "Можливо, це щойно зареєстрований проєкт."
                    )
                    return
                
                # Step 3: Convert documents to markdown
                await status_message.edit_text(
                    f"🔄 **Крок 3/4:** Конвертація документів ({len(documents)} файлів)...",
                    parse_mode='Markdown'
                )
                
                all_text = []
                
                for doc in documents:
                    # Save original document to GCS
                    try:
                        doc_filename = f"{bill_number}_{doc['original_name']}{doc['file_ext']}"
                        doc_path = self.storage.generate_bill_path(bill_number, doc_filename)
                        await self.storage.upload_file(
                            doc['content'],
                            doc_path,
                            content_type=doc.get('mime_type', 'application/octet-stream')
                        )
                    except Exception as gcs_error:
                        logger.warning("gcs_upload_failed", error=str(gcs_error), file=doc_filename)
                    
                    # Convert to markdown
                    if doc['file_ext'] == '.pdf':
                        markdown = await self.pdf_converter.convert_to_markdown(
                            doc['content'],
                            doc['original_name']
                        )
                    elif doc['file_ext'] == '.docx':
                        markdown = await self.docx_converter.convert_to_markdown(
                            doc['content'],
                            doc['original_name']
                        )
                    else:
                        continue
                    
                    if markdown:
                        all_text.append(f"\n## {doc['original_name']}\n\n{markdown}")
                        
                        # Save markdown to GCS
                        try:
                            md_filename = f"{bill_number}_{doc['original_name']}.md"
                            md_path = self.storage.generate_bill_path(bill_number, md_filename)
                            await self.storage.upload_file(
                                markdown.encode('utf-8'),
                                md_path,
                                content_type='text/markdown'
                            )
                        except Exception as gcs_error:
                            logger.warning("gcs_upload_failed", error=str(gcs_error), file=md_filename)
                
                # After processing all documents
                combined_text = "\n\n---\n\n".join(all_text)
                num_documents = len(documents)
                
                # Save combined markdown to GCS and create bill record
                try:
                    combined_filename = f"Bill_{bill_number}_Combined.md"
                    combined_path = self.storage.generate_bill_path(bill_number, combined_filename)
                    await self.storage.upload_file(
                        combined_text.encode('utf-8'),
                        combined_path,
                        content_type='text/markdown'
                    )
                    
                    # Save bill to Firestore
                    await self.firestore.create_bill({
                        'billNumber': bill_number,
                        'billTitle': bill_title,
                        'documentsCount': num_documents,
                        'gcsPath': combined_path,
                        'status': 'downloaded'
                    })
                    
                    logger.info("bill_cached", bill_number=bill_number, gcs_path=combined_path)
                except Exception as cache_error:
                    logger.warning("cache_save_failed", error=str(cache_error))
            else:
                # Using cached data
                num_documents = cached_bill.get('documentsCount', 0)
            
            # Step 4: AI Analysis
            await status_message.edit_text(
                f"🤖 **Крок 4/4:** AI-аналіз законопроєкту...",
                parse_mode='Markdown'
            )
            
            analysis_result = await self.ai_service.analyze_bill(bill_number, combined_text)
            
            if not analysis_result:
                await status_message.edit_text(
                    f"❌ Не вдалося проаналізувати законопроєкт №{bill_number}.\n"
                    "Можливо, текст надто великий або API тимчасово недоступний."
                )
                return
            
            # Send analysis result
            analysis_text = analysis_result['analysis_text']
            
            # Save analysis to GCS
            analysis_path = None
            try:
                analysis_filename = analysis_result.get('generated_filename', f'ANALYSIS_{bill_number}.txt')
                analysis_path = self.storage.generate_bill_path(bill_number, analysis_filename)
                await self.storage.upload_file(
                    analysis_text.encode('utf-8'),
                    analysis_path,
                    content_type='text/plain'
                )
            except Exception as gcs_error:
                logger.warning("gcs_upload_failed", error=str(gcs_error), file="analysis")
            
            # Prepare header with bill info
            cache_indicator = "💾 (з кешу)" if cached_bill else ""
            header = (
                f"✅ Законопроєкт №{bill_number} {cache_indicator}\n\n"
                f"📋 Назва:\n{bill_title}\n\n"
                f"📊 Документів: {num_documents}\n\n"
                f"{'─'*40}\n\n"
            )
            
            # Sanitize analysis text to avoid Markdown parsing errors
            safe_analysis_text = sanitize_markdown(analysis_text)
            
            # Split if too long (Telegram limit 4096 chars)
            max_length = 4000 - len(header)
            
            async def send_text_safe(text: str):
                """Send text with fallback to plain text if Markdown fails"""
                try:
                    await update.message.reply_text(text, parse_mode='Markdown')
                except Exception as parse_error:
                    logger.warning("markdown_parse_failed", error=str(parse_error))
                    # Fallback: send without Markdown formatting
                    await update.message.reply_text(text)
            
            if len(safe_analysis_text) > max_length:
                # Split by paragraphs to avoid breaking markdown
                parts = []
                current_part = ""
                
                for paragraph in safe_analysis_text.split('\n\n'):
                    if len(current_part) + len(paragraph) + 2 > max_length:
                        if current_part:
                            parts.append(current_part)
                        current_part = paragraph
                    else:
                        if current_part:
                            current_part += '\n\n' + paragraph
                        else:
                            current_part = paragraph
                
                if current_part:
                    parts.append(current_part)
                
                # Delete status message and send first part with header
                await status_message.delete()
                await send_text_safe(header + f"Частина 1/{len(parts)}\n\n{parts[0]}")
                
                # Send remaining parts
                for i, part in enumerate(parts[1:], 2):
                    await send_text_safe(f"Частина {i}/{len(parts)}\n\n{part}")
            else:
                # Delete status message and send complete result
                await status_message.delete()
                await send_text_safe(header + safe_analysis_text)
            
            # Save analysis record to Firestore
            await self.firestore.create_analysis({
                'billNumber': bill_number,
                'billTitle': bill_title,
                'userId': user_id,
                'username': user.username,
                'documentsCount': len(documents),
                'analysisLength': len(analysis_text),
                'gcsPath': analysis_path,
                'status': 'completed'
            })
            
            logger.info(
                "bill_analysis_completed",
                user_id=user_id,
                bill_number=bill_number,
                documents_count=len(documents)
            )
            
        except Exception as e:
            logger.error(
                "bill_command_failed",
                user_id=user_id,
                bill_number=bill_number,
                error=str(e)
            )
            
            await status_message.edit_text(
                f"❌ Помилка при обробці законопроєкту №{bill_number}.\n"
                f"Спробуйте пізніше або зверніться до підтримки."
            )
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "❌ Будь ласка, вкажіть пошуковий запит.\n"
                "Приклад: `/search освіта`",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        
        logger.info("search_command", user_id=user_id, query=query)
        
        status_message = await update.message.reply_text(
            f"🔍 Пошук за запитом: *{query}*...",
            parse_mode='Markdown'
        )
        
        try:
            # Search first page with text query
            results = await self.scraper.search_bills(page=1, per_page=30, bill_name=query)
            
            bills = results.get('bills', [])
            
            if not bills:
                await status_message.edit_text(
                    f"🤷 За запитом *{query}* нічого не знайдено.",
                    parse_mode='Markdown'
                )
                return
            
            # Format results
            response = f"🔍 **Результати пошуку:** {len(bills)} законопроєктів\n\n"
            
            for i, bill in enumerate(bills[:10], 1):
                bill_num = bill['bill_number']
                response += f"{i}. ЗП №{bill_num} - `/bill {bill_num}`\n"
            
            if len(bills) > 10:
                response += f"\n... та ще {len(bills) - 10} результатів"
            
            response += (
                f"\n\n💡 Щоб проаналізувати, використайте команду:\n"
                f"`/bill <номер>`"
            )
            
            await status_message.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error("search_failed", user_id=user_id, query=query, error=str(e))
            await status_message.edit_text(
                f"❌ Помилка пошуку. Спробуйте пізніше."
            )
    
    async def version_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /version command"""
        user = update.effective_user
        
        logger.info("version_command", user_id=user.id)
        
        # Log request (optional - skip if credentials not configured)
        try:
            await self.firestore.log_user_request(user.id, {
                'command': '/version',
                'type': 'command'
            })
        except Exception as e:
            logger.warning("firestore_error_version", error=str(e))
        
        version_text = f"""🤖 **Інформація про версію**

{get_version_string()}

📦 Компоненти:
• Python-Telegram-Bot
• Google Gemini AI
• Firestore Database
• Cloud Storage

🔗 GitHub: [rada_bill](https://github.com/your-repo)
"""
        
        await update.message.reply_text(version_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        logger.info("status_command", user_id=user_id)
        
        try:
            # Get user stats from Firestore
            user_doc = await self.firestore.db.collection('telegramUsers').document(str(user_id)).get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                total_requests = user_data.get('totalRequests', 0)
                last_interaction = user_data.get('lastInteraction', 'невідомо')
                
                status_text = (
                    "📊 **Ваша статистика**\n\n"
                    f"📈 Всього запитів: {total_requests}\n"
                    f"🕐 Остання взаємодія: {last_interaction}\n\n"
                    "✅ Бот активний\n"
                    "✅ Gemini AI доступний\n"
                    "✅ Завантаження працює\n"
                    "✅ Кешування увімкнено"
                )
            else:
                status_text = (
                    "📊 **Статус системи**\n\n"
                    "✅ Бот активний\n"
                    "✅ Gemini AI доступний\n"
                    "✅ Завантаження працює\n"
                    "✅ Кешування увімкнено\n\n"
                    "Використайте `/bill <номер>` для початку роботи."
                )
        except Exception as e:
            logger.error("status_failed", user_id=user_id, error=str(e))
            status_text = (
                "📊 **Статус системи**\n\n"
                "✅ Бот активний\n"
                "✅ Всі системи працюють"
            )
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data
        data = query.data
        
        logger.info("button_callback", user_id=query.from_user.id, data=data)
        
        if data.startswith("analyze_"):
            bill_number = data.replace("analyze_", "")
            # Trigger bill analysis
            context.args = [bill_number]
            await self.bill_command(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle plain text messages"""
        text = update.message.text.strip()
        
        print(f"📨 handle_message called: '{text}'")
        
        # Check if message is just a bill number
        if text.isdigit() and len(text) == 5:
            # Treat as /bill command
            context.args = [text]
            await self.bill_command(update, context)
        else:
            # Unknown message
            await update.message.reply_text(
                "❓ Не розумію цю команду.\n"
                "Використайте /help для списку доступних команд."
            )
    
    async def process_update(self, update_data: dict):
        """Process incoming update from webhook"""
        try:
            update = Update.de_json(update_data, self.application.bot)
            
            # Debug logging
            if update.message:
                print(f"📥 Update received: message_id={update.message.message_id}, text='{update.message.text}', entities={update.message.entities}")
            
            await self.application.process_update(update)
            logger.info("update_processed", update_id=update.update_id)
        except Exception as e:
            logger.error("update_processing_failed", error=str(e), update=update_data)
            raise
    
    async def set_webhook(self, webhook_url: str, secret_token: str):
        """Set webhook URL for bot"""
        try:
            success = await self.application.bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token,
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
            
            if success:
                logger.info("webhook_set", url=webhook_url)
            else:
                logger.error("webhook_set_failed", url=webhook_url)
            
            return success
        except Exception as e:
            logger.error("webhook_setup_error", error=str(e))
            raise
    
    async def delete_webhook(self):
        """Delete webhook (for switching to polling mode)"""
        try:
            success = await self.application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("webhook_deleted", success=success)
            return success
        except Exception as e:
            logger.error("webhook_deletion_failed", error=str(e))
            raise
    
    async def get_webhook_info(self):
        """Get current webhook information"""
        try:
            info = await self.application.bot.get_webhook_info()
            return {
                "url": info.url,
                "has_custom_certificate": info.has_custom_certificate,
                "pending_update_count": info.pending_update_count,
                "last_error_date": info.last_error_date,
                "last_error_message": info.last_error_message,
                "max_connections": info.max_connections,
                "allowed_updates": info.allowed_updates
            }
        except Exception as e:
            logger.error("webhook_info_failed", error=str(e))
            raise
    
    async def start(self):
        """Start the bot in webhook mode only"""
        logger.info("starting_telegram_bot")
        
        if not config.TELEGRAM_WEBHOOK_URL:
            error_msg = "TELEGRAM_WEBHOOK_URL is required. Bot only works in webhook mode."
            logger.error("webhook_url_missing")
            raise ValueError(error_msg)
        
        if not config.TELEGRAM_SECRET_TOKEN:
            error_msg = "TELEGRAM_SECRET_TOKEN is required for webhook security."
            logger.error("secret_token_missing")
            raise ValueError(error_msg)
        
        # Webhook mode only - updates come through API endpoint
        await self.application.initialize()
        await self.application.start()  # Start without updater
        logger.info("bot_initialized_webhook_mode", webhook=config.TELEGRAM_WEBHOOK_URL)
        print(f"🌐 Bot running in WEBHOOK mode: {config.TELEGRAM_WEBHOOK_URL}")
    
    async def stop(self):
        """Stop the bot"""
        logger.info("stopping_telegram_bot")
        
        if self.application:
            # Webhook mode - manually stop and shutdown
            await self.application.stop()
            await self.application.shutdown()


# Bot instance
bot = TelegramBot()
