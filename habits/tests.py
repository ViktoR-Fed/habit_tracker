from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Habit
from .serializers import HabitSerializer

User = get_user_model()


class HabitModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", telegram_chat_id="123456789"
        )

        self.habit_data = {
            "user": self.user,
            "place": "Дом",
            "time": "07:00:00",
            "action": "Утренняя зарядка",
            "is_pleasant": False,
            "periodicity": 1,
            "time_limit": 60,
            "is_public": True,
        }

    def test_create_habit(self):
        habit = Habit.objects.create(**self.habit_data)
        self.assertEqual(habit.action, "Утренняя зарядка")
        self.assertEqual(habit.user, self.user)

    def test_habit_validation_time_limit(self):
        self.habit_data["time_limit"] = 150
        with self.assertRaises(Exception):
            Habit.objects.create(**self.habit_data)

    def test_habit_str_method(self):
        habit = Habit.objects.create(**self.habit_data)
        expected_str = f"{habit.action} - {habit.user.username}"
        self.assertEqual(str(habit), expected_str)


class HabitAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.habit_data = {
            "place": "Дом",
            "time": "07:00:00",
            "action": "Утренняя зарядка",
            "is_pleasant": False,
            "periodicity": 1,
            "time_limit": 60,
        }

    def test_create_habit(self):
        response = self.client.post("habits/create/", self.habit_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["action"], "Утренняя зарядка")

    def test_public_habits(self):
        Habit.objects.create(user=self.user, **self.habit_data, is_public=True)
        self.client.logout()
        response = self.client.get("habits/public/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_habit_update(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        update_data = {"action": "Вечерняя пробежка", "time_limit": 90}
        response = self.client.patch(f"habits/{habit.id}/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "Вечерняя пробежка")

    def test_habit_delete(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.delete(f"habits/{habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
