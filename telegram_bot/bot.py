import logging
from typing import Optional

from asgiref.sync import sync_to_async
from django.conf import settings
from telegram import Bot, Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from users.models import User

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env файле")
        self.bot = Bot(token=self.token)
        self.application: Optional[Application] = None

    @sync_to_async
    def get_or_create_user(self, user_id: int, username: str):
        """Получение или создание пользователя в БД (синхронная обертка)"""
        user, created = User.objects.get_or_create(
            username=f"telegram_{user_id}",
            defaults={
                "telegram_chat_id": str(user_id),
                "telegram_username": username,
                "email": f"telegram_{user_id}@temp.com",
            },
        )
        if not created:
            user.telegram_chat_id = str(user_id)
            user.telegram_username = username
            user.save()
        return user, created

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or str(user_id)

        try:
            user, created = await self.get_or_create_user(user_id, username)

            welcome_message = (
                f"👋 Привет, {user.username}!\n\n"
                "Я бот для управления привычками. Я буду напоминать тебе о необходимости выполнить привычки.\n\n"
                "Используй веб-интерфейс для управления привычками, а я буду отправлять тебе уведомления! 📱\n\n"
                "Для справки используй команду /help"
            )
            await update.message.reply_text(welcome_message)
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = (
            "🤖 **Помощь по боту**\n\n"
            "Я помогаю тебе следить за привычками! 💪\n\n"
            "**Команды:**\n"
            "/start - начать работу с ботом\n"
            "/help - показать эту справку\n\n"
            "**Как это работает:**\n"
            "1️⃣ Создай привычки в веб-интерфейсе\n"
            "2️⃣ Укажи время выполнения\n"
            "3️⃣ Я буду присылать тебе напоминания! ⏰\n\n"
            "Удачи в формировании полезных привычек! 🎯"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик неизвестных команд"""
        await update.message.reply_text(
            "❌ Неизвестная команда.\n"
            "Используйте /start или /help для получения справки."
        )

    async def send_notification_async(self, chat_id: str, message: str) -> bool:
        """Асинхронная отправка уведомления"""
        try:
            await self.bot.send_message(
                chat_id=chat_id, text=message, parse_mode="Markdown"
            )
            logger.info(f"✅ Notification sent to {chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send notification to {chat_id}: {e}")
            return False

    def setup(self):
        """Настройка бота"""
        try:
            self.application = Application.builder().token(self.token).build()

            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(
                MessageHandler(filters.COMMAND, self.unknown_command)
            )

            logger.info("✅ Telegram bot setup completed")
        except Exception as e:
            logger.error(f"❌ Failed to setup bot: {e}")
            raise

    def run(self):
        """Запуск бота"""
        if not self.application:
            self.setup()

        logger.info("🚀 Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


# Создание экземпляра бота
try:
    bot_instance = TelegramBot()
except Exception as e:
    logger.error(f"❌ Failed to create bot instance: {e}")
    bot_instance = None
