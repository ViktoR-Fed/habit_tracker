import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from users.models import User

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.bot = Bot(token=self.token)
        self.application = None

    async def start(self, update: Update, context):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or str(user_id)

        try:
            # Обновляем данные пользователя в БД
            user = await self.get_or_create_user(user_id, username)
            await update.message.reply_text(
                f"👋 Привет, {user.username}!\n\n"
                "Я бот для управления привычками. Я буду напоминать тебе о необходимости выполнить привычки.\n\n"
                "Используй веб-интерфейс для управления привычками, а я буду отправлять тебе уведомления! 📱"
            )
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

    async def get_or_create_user(self, user_id, username):
        """Получение или создание пользователя в БД"""
        user, created = User.objects.get_or_create(
            username=f"telegram_{user_id}",
            defaults={"telegram_chat_id": str(user_id), "telegram_username": username},
        )
        if not created and not user.telegram_chat_id:
            user.telegram_chat_id = str(user_id)
            user.telegram_username = username
            user.save()
        return user

    async def help_command(self, update: Update, context):
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

    async def unknown_command(self, update: Update, context):
        """Обработчик неизвестных команд"""
        await update.message.reply_text(
            "Неизвестная команда. Используйте /start или /help для получения справки."
        )

    def send_notification(self, chat_id: str, message: str):
        """Отправка уведомления пользователю"""
        try:
            self.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Notification sent to {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to {chat_id}: {e}")
            return False

    def setup(self):
        """Настройка бота"""
        self.application = Application.builder().token(self.token).build()

        # Регистрация обработчиков
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(
            MessageHandler(filters.COMMAND, self.unknown_command)
        )

    def run(self):
        """Запуск бота"""
        if not self.application:
            self.setup()
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


# Создание экземпляра бота
bot_instance = TelegramBot()
