from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import CharField, CASCADE, ForeignKey, DecimalField, PositiveSmallIntegerField, TextField, \
    DateTimeField
from django.db.models.enums import TextChoices

from apps.models import User
from apps.models.base import UUIDBaseModel, CreatedBaseModel
from django.utils.translation import gettext_lazy as _


class Language(UUIDBaseModel):
    """Модель для языков"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Название языка"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("Код языка (ISO 639)"))

    class Meta:
        verbose_name = _("Язык")
        verbose_name_plural = _("Языки")
        ordering = ['name']

    def __str__(self):
        return self.name


class TranslationRate(CreatedBaseModel):
    translator = ForeignKey(
        'apps.Interpreter',
        CASCADE,
        related_name="rates"
    )

    translation_type = ForeignKey(
        'apps.TranslationType',
        CASCADE
    )

    rate = DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        unique_together = ('translator', 'translation_type')


class City(UUIDBaseModel):
    name = CharField(max_length=155, unique=True)
    country = CharField(max_length=155, blank=True)

    def __str__(self):
        return f"{self.name} ({self.country})" if self.country else self.name


class Specialization(UUIDBaseModel):
    name = CharField(max_length=155, unique=True)

    def __str__(self):
        return self.name


class Availability(CreatedBaseModel):
    """Модель доступности переводчика"""

    class AvailabilityType(TextChoices):
        AVAILABLE = 'available', _('Доступен')
        BUSY = 'busy', _('Занят')

    translator = ForeignKey(
        'apps.Interpreter',
        CASCADE,
        related_name='availabilities',
        verbose_name=_('Переводчик')
    )

    start_datetime = DateTimeField(verbose_name=_('Дата и время начала'))
    end_datetime = DateTimeField(verbose_name=_('Дата и время окончания'))

    type = CharField(
        max_length=20,
        choices=AvailabilityType.choices,  # type: ignore
        default=AvailabilityType.AVAILABLE,
        verbose_name=_('Тип доступности')
    )

    # Повторяющиеся события
    # is_recurring = BooleanField(
    #     default=False,
    #     verbose_name='Повторяющееся событие'
    # )
    #
    # recurrence_rule = TextField(
    #     blank=True,
    #     null=True,
    #     help_text='Правило повторения в формате iCalendar RRULE',
    #     verbose_name='Правило повторения'
    # )
    #
    # recurrence_end_date = DateTimeField(
    #     blank=True,
    #     null=True,
    #     verbose_name='Дата окончания повторений'
    # )

    # Интеграция с Google Calendar
    google_event_id = CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_('ID события Google Calendar')
    )

    google_sync_token = TextField(
        blank=True,
        null=True,
        verbose_name=_('Токен синхронизации Google')
    )

    last_synced_at = DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Последняя синхронизация')
    )

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


class Review(CreatedBaseModel):
    client = ForeignKey(
        'apps.Client',
        CASCADE,
        related_name='reviews'
    )
    interpreter = ForeignKey('apps.Interpreter', CASCADE)
    score = PositiveSmallIntegerField(
        validators=[MinValueValidator(1),
                    MaxValueValidator(5)]
    )
    comment = TextField(blank=True)
