from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_time_limit(value):
    """Валидатор времени выполнения (не больше 120 секунд)"""
    if value > 120:
        raise ValidationError(
            _("Время выполнения не должно превышать 120 секунд"),
            code="time_limit_exceeded",
        )


def validate_periodicity(value):
    """Валидатор периодичности (1-7 дней)"""
    if value < 1 or value > 7:
        raise ValidationError(
            _("Периодичность должна быть от 1 до 7 дней"), code="invalid_periodicity"
        )
