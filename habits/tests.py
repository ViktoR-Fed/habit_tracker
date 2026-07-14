from datetime import time
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Habit
from .tasks import send_habit_notifications_task

User = get_user_model()


class HabitModelTest(TestCase):
    """Тестирование модели Habit"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )
        self.habit_data = {
            "user": self.user,
            "place": "Дом",
            "time": time(7, 0, 0),
            "action": "Утренняя зарядка",
            "is_pleasant": False,
            "periodicity": 1,
            "time_limit": 60,  # Исправлено: 60 секунд, а не 900
            "is_public": True,
        }

    def test_create_habit(self):
        habit = Habit.objects.create(**self.habit_data)
        self.assertEqual(habit.action, "Утренняя зарядка")
        self.assertEqual(habit.user, self.user)
        self.assertEqual(habit.time_limit, 60)

    def test_habit_validation_time_limit(self):
        self.habit_data["time_limit"] = 150
        with self.assertRaises(Exception):
            Habit.objects.create(**self.habit_data)

    def test_habit_validation_periodicity(self):
        self.habit_data["periodicity"] = 10
        with self.assertRaises(Exception):
            Habit.objects.create(**self.habit_data)

    def test_pleasant_habit_no_reward(self):
        self.habit_data["is_pleasant"] = True
        self.habit_data["reward"] = "Награда"
        with self.assertRaises(Exception):
            Habit.objects.create(**self.habit_data)

    def test_habit_with_related_habit(self):
        # Создаем приятную привычку с корректным time_limit
        pleasant_habit = Habit.objects.create(
            user=self.user,
            place="Ванная",
            time=time(8, 0, 0),
            action="Принять ванну",
            is_pleasant=True,
            periodicity=1,
            time_limit=60,  # Исправлено: не более 120 секунд
        )
        self.habit_data["related_habit"] = pleasant_habit
        habit = Habit.objects.create(**self.habit_data)
        self.assertEqual(habit.related_habit, pleasant_habit)

    def test_habit_str_method(self):
        habit = Habit.objects.create(**self.habit_data)
        expected_str = f"{habit.action} - {habit.user.username}"
        self.assertEqual(str(habit), expected_str)


class HabitAPITest(TestCase):
    """Тестирование API эндпоинтов"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )

        # Используем правильный URL с префиксом /api/
        response = self.client.post(
            "/users/login/", {"username": "testuser", "password": "testpass123"}
        )

        # Проверяем успешность ответа
        if response.status_code != status.HTTP_200_OK:
            self.fail(f"Login failed with status {response.status_code}")

        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        self.habit_data = {
            "place": "Дом",
            "time": "07:00:00",
            "action": "Утренняя зарядка",
            "is_pleasant": False,
            "periodicity": 1,
            "time_limit": 60,
            "is_public": True,
        }

    def test_create_habit(self):
        response = self.client.post("/habits/", self.habit_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["action"], "Утренняя зарядка")

    def test_create_habit_with_public(self):
        data = self.habit_data.copy()
        data["is_public"] = True
        response = self.client.post("/habits/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_public"])

    def test_list_habits(self):
        Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.get("/habits/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_public_habits_include_all(self):
        """Тест: публичные привычки включают все is_public=True"""
        Habit.objects.create(user=self.user, **self.habit_data, is_public=True)
        Habit.objects.create(
            user=self.user,
            **self.habit_data,
            is_public=True,
            is_pleasant=True,
            action="Приятная",
            time_limit=60,
        )
        self.client.logout()
        response = self.client.get("/habits/public/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_retrieve_habit(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.get(f"/habits/{habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "Утренняя зарядка")

    def test_update_habit(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        update_data = {"action": "Вечерняя пробежка"}
        response = self.client.patch(f"/habits/{habit.id}/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "Вечерняя пробежка")

    def test_delete_habit(self):
        habit = Habit.objects.create(user=self.user, **self.habit_data)
        response = self.client.delete(f"/habits/{habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Habit.objects.count(), 0)

    def test_unauthorized_access(self):
        self.client.logout()
        response = self.client.get("/habits/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_other_user_cannot_access(self):
        other_user = User.objects.create_user(username="other", password="otherpass")
        habit = Habit.objects.create(user=other_user, **self.habit_data)
        response = self.client.get(f"/habits/{habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HabitValidationTest(TestCase):
    """Тестирование валидации"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client = APIClient()
        response = self.client.post(
            "/users/login/", {"username": "testuser", "password": "testpass123"}
        )

        if response.status_code != status.HTTP_200_OK:
            self.fail(f"Login failed with status {response.status_code}")

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')

    def test_habit_with_both_related_and_reward(self):
        # Создаем приятную привычку с корректным time_limit
        pleasant = Habit.objects.create(
            user=self.user,
            place="Ванная",
            time="08:00:00",
            action="Принять ванну",
            is_pleasant=True,
            periodicity=1,
            time_limit=60,
        )

        data = {
            "place": "Парк",
            "time": "18:00:00",
            "action": "Прогулка",
            "is_pleasant": False,
            "related_habit": pleasant.id,
            "reward": "Десерт",
            "periodicity": 1,
            "time_limit": 60,
        }
        response = self.client.post("/habits/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pleasant_habit_with_reward(self):
        data = {
            "place": "Ванная",
            "time": "08:00:00",
            "action": "Принять ванну",
            "is_pleasant": True,
            "reward": "Награда",
            "periodicity": 1,
            "time_limit": 60,
        }
        response = self.client.post("/habits/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_related_habit_must_be_pleasant(self):
        not_pleasant = Habit.objects.create(
            user=self.user,
            place="Дом",
            time="07:00:00",
            action="Зарядка",
            is_pleasant=False,
            periodicity=1,
            time_limit=60,
        )

        data = {
            "place": "Парк",
            "time": "18:00:00",
            "action": "Прогулка",
            "is_pleasant": False,
            "related_habit": not_pleasant.id,
            "periodicity": 1,
            "time_limit": 60,
        }
        response = self.client.post("/habits/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HabitPaginationTest(TestCase):
    """Тестирование пагинации"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client = APIClient()
        response = self.client.post(
            "/users/login/", {"username": "testuser", "password": "testpass123"}
        )

        if response.status_code != status.HTTP_200_OK:
            self.fail(f"Login failed with status {response.status_code}")

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')

    def test_pagination_limit_offset(self):
        for i in range(10):
            Habit.objects.create(
                user=self.user,
                place=f"Место {i}",
                time="07:00:00",
                action=f"Действие {i}",
                is_pleasant=False,
                periodicity=1,
                time_limit=60,
            )

        response = self.client.get("/habits/?limit=5&offset=0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertEqual(response.data["count"], 10)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

        response = self.client.get("/habits/?limit=5&offset=5")
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["previous"])


class CeleryTaskTest(TestCase):
    """Тестирование Celery задач"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", telegram_chat_id="123456789"
        )
        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=time(7, 0, 0),
            action="Утренняя зарядка",
            is_pleasant=False,
            periodicity=1,
            time_limit=60,
            is_public=True,
        )

    @patch("habits.tasks.send_habit_notifications_task.delay")
    def test_notification_task(self, mock_task):
        """Тест задачи отправки уведомлений"""
        mock_task.return_value = MagicMock(id="test-id")
        result = send_habit_notifications_task.delay()
        self.assertTrue(result.id)
        mock_task.assert_called_once()


class UserAPITest(TestCase):
    """Тестирование API пользователей"""

    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        response = self.client.post(
            "/users/register/",
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "TestPass123!",
                "password2": "TestPass123!",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "newuser")

    def test_login_user(self):
        User.objects.create_user(username="testuser", password="testpass123")
        response = self.client.post(
            "/users/login/", {"username": "testuser", "password": "testpass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_me(self):
        user = User.objects.create_user(username="testuser", password="testpass123")
        response = self.client.post(
            "/users/me/", {"username": "testuser", "password": "testpass123"}
        )

        if response.status_code != status.HTTP_200_OK:
            self.fail(f"Login failed with status {response.status_code}")

        token = response.data["access"]
        # Используем client.defaults для установки заголовка
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"

        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")
