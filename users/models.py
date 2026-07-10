from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    telegram_chat_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Telegram ID"
    )
    telegram_username = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Telegram Username"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username
