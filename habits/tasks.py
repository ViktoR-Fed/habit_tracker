import logging
from datetime import datetime

from celery import shared_task
from django.utils import timezone

from telegram_bot.utils import send_habit_notifications

logger = logging.getLogger(__name__)


@shared_task
def send_habit_notifications():
    """Отправка уведомлений о привычках"""
    try:
        sent_count = send_habit_notifications()
        logger.info(f"Sent {sent_count} habit notifications")
        return f"Sent {sent_count} notifications"
    except Exception as e:
        logger.error(f"Error sending notifications: {e}")
        raise


@shared_task
def check_habits_periodicity():
    """Проверка периодичности привычек (запасная задача)"""
    from datetime import timedelta

    from habits.models import Habit

    now = timezone.now()
    week_ago = now - timedelta(days=7)

    # Проверяем привычки, которые не выполнялись более 7 дней
    habits = Habit.objects.filter(
        created_at__lte=week_ago, user__telegram_chat_id__isnull=False
    )

    for habit in habits:
        # Здесь можно реализовать логику для дополнительных напоминаний
        pass

    return f"Checked {habits.count()} habits"
