from django.urls import path

from .views import (
    HabitListByPeriodView,
    HabitListCreateView,
    HabitRetrieveUpdateDestroyView,
    PublicHabitListView,
)

urlpatterns = [
    path("create/", HabitListCreateView.as_view(), name="habitcreate"),
    path("<int:pk>/", HabitRetrieveUpdateDestroyView.as_view(), name="habit-detail"),
    path("public/", PublicHabitListView.as_view(), name="public-habits"),
    path("by-time/", HabitListByPeriodView.as_view(), name="habits-by-time"),
]
