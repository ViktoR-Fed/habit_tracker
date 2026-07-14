from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .validators import validate_periodicity, validate_time_limit


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Пользователь",
    )
    place = models.CharField(max_length=255, verbose_name="Место выполнения")
    time = models.TimeField(verbose_name="Время выполнения")
    action = models.CharField(max_length=255, verbose_name="Действие")
    is_pleasant = models.BooleanField(
        default=False, verbose_name="Признак приятной привычки"
    )
    related_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Связанная привычка",
        related_name="related_to",
    )
    periodicity = models.PositiveIntegerField(
        default=1,
        validators=[validate_periodicity],
        verbose_name="Периодичность (в днях)",
    )
    reward = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Вознаграждение"
    )
    time_limit = models.PositiveIntegerField(
        validators=[validate_time_limit],
        verbose_name="Время на выполнение (в секундах)",
    )
    is_public = models.BooleanField(default=False, verbose_name="Публичная привычка")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["-created_at"]

    def clean(self):
        # Исключить одновременный выбор связанной привычки и вознаграждения
        if self.related_habit and self.reward:
            raise ValidationError(
                "Нельзя одновременно выбирать связанную привычку и вознаграждение"
            )

        # У приятной привычки не может быть вознаграждения или связанной привычки
        if self.is_pleasant:
            if self.reward:
                raise ValidationError("Приятная привычка не может иметь вознаграждение")
            if self.related_habit:
                raise ValidationError(
                    "Приятная привычка не может иметь связанную привычку"
                )

        # В связанные привычки могут попадать только привычки с признаком приятной привычки
        if self.related_habit and not self.related_habit.is_pleasant:
            raise ValidationError("Связанная привычка должна быть приятной")

        # Проверка на цикличность
        if self.related_habit and self.related_habit == self:
            raise ValidationError("Привычка не может быть связана сама с собой")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.action} - {self.user.username}"
