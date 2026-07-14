from rest_framework import generics, permissions, status

from .models import Habit
from .pagination import HabitPagination
from .permissions import IsOwner
from .serializers import HabitSerializer, PublicHabitSerializer


class HabitListCreateView(generics.ListCreateAPIView):
    """Список привычек пользователя и создание новой"""

    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HabitPagination

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HabitRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, редактирование и удаление привычки"""

    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    """Список публичных привычек"""

    serializer_class = PublicHabitSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = HabitPagination

    def get_queryset(self):
        return Habit.objects.filter(is_public=True)


class HabitListByPeriodView(generics.ListAPIView):
    """Список привычек для отправки уведомлений"""

    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HabitPagination

    def get_queryset(self):
        from datetime import datetime

        current_time = datetime.now().time()
        return Habit.objects.filter(
            user=self.request.user,
            time__hour=current_time.hour,
            time__minute=current_time.minute,
        )
