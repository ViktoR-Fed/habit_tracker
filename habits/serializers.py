from django.db import models
from rest_framework import serializers

from .models import Habit


class HabitSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    is_public = serializers.BooleanField(read_only=True)

    class Meta:
        model = Habit
        fields = (
            "id",
            "user",
            "place",
            "time",
            "action",
            "is_pleasant",
            "related_habit",
            "periodicity",
            "reward",
            "time_limit",
            "is_public",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate(self, data):
        # Проверка на одновременный выбор связанной привычки и вознаграждения
        if data.get("related_habit") and data.get("reward"):
            raise serializers.ValidationError(
                "Нельзя одновременно выбирать связанную привычку и вознаграждение"
            )

        # Проверка для приятной привычки
        if data.get("is_pleasant"):
            if data.get("reward"):
                raise serializers.ValidationError(
                    "Приятная привычка не может иметь вознаграждение"
                )
            if data.get("related_habit"):
                raise serializers.ValidationError(
                    "Приятная привычка не может иметь связанную привычку"
                )

        # Проверка связанной привычки
        if data.get("related_habit"):
            if not data["related_habit"].is_pleasant:
                raise serializers.ValidationError(
                    "Связанная привычка должна быть приятной"
                )
            if data["related_habit"] == data.get("instance"):
                raise serializers.ValidationError(
                    "Привычка не может быть связана сама с собой"
                )

        return data


class PublicHabitSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Habit
        fields = (
            "id",
            "user_username",
            "place",
            "time",
            "action",
            "periodicity",
            "time_limit",
            "created_at",
        )
        read_only_fields = fields
