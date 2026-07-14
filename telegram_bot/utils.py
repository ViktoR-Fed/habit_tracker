import asyncio
import logging

from asgiref.sync import sync_to_async

from habits.models import Habit
from telegram_bot.bot import bot_instance

logger = logging.getLogger(__name__)


@sync_to_async
def get_habits_for_notification():
    """Получение привычек для уведомлений (синхронная обертка)"""
    from datetime import datetime

    current_time = datetime.now().time()

    return list(
        Habit.objects.select_related("user").filter(
            time__hour=current_time.hour,
            time__minute=current_time.minute,
        )
    )


def create_habit_message(habit):
    """Создание сообщения для уведомления"""
    message = f"⏰ **Напоминание о привычке!**\n\n"
    message += f"📝 **Действие:** {habit.action}\n"
    message += f"📍 **Место:** {habit.place}\n"
    message += f"⏱️ **Время:** {habit.time.strftime('%H:%M')}\n"
    message += f"📅 **Периодичность:** {habit.periodicity} дн.\n"

    if habit.is_pleasant:
        message += "😊 **Приятная привычка**\n"

    if habit.reward:
        message += f"🎁 **Вознаграждение:** {habit.reward}\n"

    if habit.related_habit:
        message += f"🔗 **Связанная привычка:** {habit.related_habit.action}\n"

    message += f"\n💪 **Выполни привычку и стань лучше!**"
    return message


def send_habit_notifications():
    """Отправка уведомлений о привычках (синхронная обертка)"""
    from datetime import datetime

    try:
        # Получаем привычки синхронно
        habits = Habit.objects.select_related("user").filter(
            time__hour=datetime.now().time().hour,
            time__minute=datetime.now().time().minute,
        )

        sent_count = 0
        for habit in habits:
            user = habit.user
            if user.telegram_chat_id:
                message = create_habit_message(habit)
                # Используем асинхронную отправку через asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(
                        bot_instance.send_notification_async(
                            user.telegram_chat_id, message
                        )
                    )
                    loop.close()
                    if success:
                        sent_count += 1
                        logger.info(f"Notification sent for habit {habit.id}")
                except Exception as e:
                    logger.error(f"Error sending notification: {e}")

        return sent_count
    except Exception as e:
        logger.error(f"Error in send_habit_notifications: {e}")
        return 0
