import asyncio
from unittest.mock import AsyncMock, patch

from django.test import TestCase

from telegram_bot.bot import TelegramBot
from users.models import User


class TelegramBotTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", telegram_chat_id="123456789"
        )
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    @patch("telegram_bot.bot.Bot")
    def test_bot_initialization(self, MockBot):
        """Тест инициализации бота"""
        # Создаем мок с необходимыми атрибутами
        mock_bot_instance = AsyncMock()
        mock_bot_instance.send_message = AsyncMock()
        MockBot.return_value = mock_bot_instance

        # Создаем бота
        bot = TelegramBot()
        self.assertIsNotNone(bot)

    @patch("telegram_bot.bot.bot_instance.bot")
    def test_send_notification_success(self, mock_bot):
        """Тест успешной отправки уведомления"""
        # Создаем экземпляр бота
        bot = TelegramBot()

        # Настраиваем мок
        mock_bot.send_message = AsyncMock(return_value=None)

        # Отправляем уведомление
        result = self.loop.run_until_complete(
            bot.send_notification_async("123456789", "Тест")
        )

        self.assertTrue(result)
        mock_bot.send_message.assert_called_once_with(
            chat_id="123456789", text="Тест", parse_mode="Markdown"
        )

    @patch("telegram_bot.bot.bot_instance.bot")
    def test_send_notification_error(self, mock_bot):
        """Тест ошибки отправки уведомления"""
        bot = TelegramBot()

        # Настраиваем мок с ошибкой
        mock_bot.send_message = AsyncMock(side_effect=Exception("Network error"))

        # Отправляем уведомление
        result = self.loop.run_until_complete(
            bot.send_notification_async("123456789", "Тест")
        )

        self.assertFalse(result)
        mock_bot.send_message.assert_called_once()

    def test_create_habit_message(self):
        """Тест создания сообщения для привычки"""
        from datetime import time

        from habits.models import Habit

        habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=time(7, 0, 0),
            action="Утренняя зарядка",
            is_pleasant=False,
            periodicity=1,
            time_limit=60,
            is_public=True,
        )

        from telegram_bot.utils import create_habit_message

        message = create_habit_message(habit)

        self.assertIn("⏰ **Напоминание о привычке!**", message)
        self.assertIn("Утренняя зарядка", message)
        self.assertIn("Дом", message)
