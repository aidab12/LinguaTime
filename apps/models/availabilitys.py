from django.core.exceptions import ValidationError
from django.db.models import ForeignKey, TextChoices, CASCADE, DateTimeField, CharField, TextField, BooleanField

from apps.models.base import CreatedBaseModel
from django.utils.translation import gettext_lazy as _


class Availability(CreatedBaseModel):
    """Модель доступности переводчика"""

    class AvailabilityType(TextChoices):
        AVAILABLE = 'available', _('Доступен')
        BUSY = 'busy', _('Занят')


    start_datetime = DateTimeField(_('Дата и время начала'))
    end_datetime = DateTimeField(_('Дата и время окончания'))
    type = CharField(_('Тип доступности'), max_length=20, choices=AvailabilityType.choices,
                     default=AvailabilityType.AVAILABLE
                     )

    # Интеграция с Google Calendar
    google_event_id = CharField(_('ID события Google Calendar'), max_length=255, blank=True, null=True, unique=True)
    google_sync_token = TextField(_('Токен синхронизации Google'), blank=True, null=True)
    last_synced_at = DateTimeField(_('Последняя синхронизация'), blank=True, null=True)
    is_google_calendar_event = BooleanField(_('Событие из Google Calendar'), default=False)


    translator = ForeignKey('apps.Interpreter', CASCADE, related_name='availabilities', verbose_name=_('Переводчик'))

    class Meta:
        verbose_name = _('Доступность переводчика')
        verbose_name_plural = _('Доступности переводчиков')
        ordering = ['-start_datetime']

    def __str__(self):
        return f"{self.translator} - {self.get_type_display()} ({self.start_datetime.date()})"

    def clean(self):
        """Валидация на уровне модели"""
        if self.end_datetime and self.start_datetime:
            if self.end_datetime <= self.start_datetime:
                raise ValidationError({
                    'end_datetime': 'Дата окончания должна быть позже даты начала'
                })

    def save(self, *args, **kwargs):
        """Переопределение save для вызова clean()"""
        self.clean()
        super().save(*args, **kwargs)
