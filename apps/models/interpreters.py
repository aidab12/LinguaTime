from django.core.exceptions import ValidationError
from django.db.models import (BooleanField, DateTimeField,
                              TextChoices, TextField)
from django.db.models import CASCADE, CharField, ForeignKey
from django.utils.translation import gettext_lazy as _

from apps.models.base import UUIDBaseModel, CreatedBaseModel


class Availability(CreatedBaseModel):
    """Модель доступности переводчика"""

    class AvailabilityType(TextChoices):
        AVAILABLE = 'available', _('Доступен')
        BUSY = 'busy', _('Занят')

    start_datetime = DateTimeField(_('Дата и время начала'))
    end_datetime = DateTimeField(_('Дата и время окончания'))
    type = CharField(_('Тип доступности'), max_length=20, choices=AvailabilityType.choices,
                     default=AvailabilityType.AVAILABLE)

    # Интеграция с Google Calendar
    google_event_id = CharField(_('ID события Google Calendar'), max_length=255, blank=True, null=True, unique=True)
    google_sync_token = TextField(_('Токен синхронизации Google'), blank=True, null=True)
    last_synced_at = DateTimeField(_('Последняя синхронизация'), blank=True, null=True)
    is_google_calendar_event = BooleanField(_('Событие из Google Calendar'), default=False)

    translator = ForeignKey('apps.Interpreter', CASCADE, related_name='availabilities')

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

    def save(self, *args, **kwargs):  # TODO remove method
        """Переопределение save для вызова clean()"""
        self.clean()
        super().save(*args, **kwargs)


class Language(UUIDBaseModel):
    """Модель для языков"""
    name = CharField(max_length=100)

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
        ordering = ['name']

    def __str__(self):
        return self.name


class LanguagePair(UUIDBaseModel):
    source = ForeignKey('apps.Language', CASCADE, related_name='source_pairs')
    target = ForeignKey('apps.Language', CASCADE, related_name='target_pairs')

    class Meta:
        unique_together = ('source', 'target')

    def __str__(self):
        return f'{self.source} → {self.target}'


class TranslationType(UUIDBaseModel):
    name = CharField(max_length=100)
