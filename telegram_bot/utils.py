import logging

from habits.models import Habit
from telegram_bot.bot import bot_instance
from users.models import User

logger = logging.getLogger(__name__)


def send_habit_notifications():
    """Отправка уведомлений о привычках"""
    from datetime import datetime, timedelta

    import pytz

    now = datetime.now()
    current_time = now.time()

    # Получаем все привычки, которые должны выполняться сейчас
    habits = Habit.objects.select_related("user").filter(
        time__hour=current_time.hour,
        time__minute=current_time.minute,
    )

    sent_count = 0
    for habit in habits:
        # Проверяем периодичность
        days_since_last = (now.date() - habit.created_at.date()).days
        if days_since_last % habit.periodicity != 0:
            continue

        # Отправляем уведомление
        user = habit.user
        if user.telegram_chat_id:
            message = create_habit_message(habit)
            success = bot_instance.send_notification(user.telegram_chat_id, message)
            if success:
                sent_count += 1
                logger.info(
                    f"Notification sent for habit {habit.id} to user {user.username}"
                )

    return sent_count


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
