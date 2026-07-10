from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение: только владелец может изменять привычку.
    Публичные привычки доступны для чтения всем.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user
        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """Разрешение: только владелец имеет доступ"""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
