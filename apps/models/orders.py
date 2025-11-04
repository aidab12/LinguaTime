from django.core.exceptions import ValidationError
from django.db.models import TextChoices, ForeignKey, PROTECT, DateTimeField, CharField, TextField, URLField, \
    PositiveSmallIntegerField, ManyToManyField, BooleanField, DecimalField, CASCADE
from django.utils.translation import gettext_lazy as _

from apps.models.base import CreatedBaseModel, UUIDBaseModel


class Order(CreatedBaseModel):
    """Модель заказа на перевод"""

    # ===== CHOICES =====

    class LocationType(TextChoices):
        ONSITE = 'onsite', _('На Месте')
        ONLINE = 'online', _('Онлайн')

    class TranslationType(TextChoices):
        SIMULTANEOUS = 'simultaneous', _('Синхронный')
        CONSECUTIVE = 'consecutive', _('Последовательный')
        WRITTEN = 'written', _('Письменный')

    class FormalityLevel(TextChoices):
        BUSINESS = 'business', _('Рабочий')
        OFFICIAL = 'official', _('Официальный')

    class GenderRequirement(TextChoices):
        NO_PREFERENCE = 'no_preference', _('Не важно')
        MALE = 'male', _('Мужчина')
        FEMALE = 'female', _('Женщина')

    class OrderStatus(TextChoices):
        NEW = 'new', _('Новый')
        SEARCHING = 'searching', _('В поиске переводчика')
        ASSIGNED = 'assigned', _('Переводчик назначен')
        COMPLETED = 'completed', _('Завершён')
        CANCELLED = 'cancelled', _('Отменён')

    class PlatformChoises(TextChoices):
        GOOGLE_MEET = 'google_meet', 'Google-Meet'
        ZOOM = 'zoom', 'Zoom'
        SKYPE = 'skype', 'Skype'
        TELEGRAM = 'telegram', 'Telegram'

    # ===== ОСНОВНЫЕ ПОЛЯ =====

    client = ForeignKey(
        'apps.Client',
        PROTECT,  # Нельзя удалить клиента с заказами
        related_name='orders',
        verbose_name=_('Клиент')
    )

    # ===== ВРЕМЯ И ДАТА =====

    start_datetime = DateTimeField(
        verbose_name=_('Дата и время начала')
    )

    end_datetime = DateTimeField(
        verbose_name=_('Дата и время окончания')
    )

    # ===== ЛОКАЦИЯ =====

    location_type = CharField(
        max_length=20,
        choices=LocationType.choices,
        verbose_name=_('Тип локации')
    )

    city = ForeignKey(
        'apps.City',
        PROTECT,
        blank=True,
        null=True,
        verbose_name=_('Город'),
        help_text=_('Обязательно, если не онлайн')
    )

    address = TextField(
        blank=True,
        verbose_name=_('Адрес'),
        help_text=_('Опционально')
    )

    # ===== ДЕТАЛИ ОНЛАЙН =====

    online_platform = CharField(
        max_length=100,
        choices=PlatformChoises.choices,
        blank=True,
        verbose_name=_('Платформа'),
    )

    online_link = URLField(
        blank=True,
        verbose_name='Ссылка на встречу'
    )

    # ===== ТИП ПЕРЕВОДА =====

    translation_type = CharField(
        max_length=20,
        choices=TranslationType.choices,
        verbose_name=_('Тип перевода')
    )

    interpreter_count = PositiveSmallIntegerField(
        default=1,
        verbose_name=_('Количество переводчиков')
    )

    # specialization = ? # TASK

    # ===== ЯЗЫКИ (многие-ко-многим) =====

    languages = ManyToManyField(
        'apps.Language',
        related_name='orders',
        verbose_name=_('Языки перевода'),
        help_text=_('Можно выбрать несколько языковых пар')
    )

    # ===== УРОВЕНЬ ОФИЦИАЛЬНОСТИ =====

    formality_level = CharField(
        max_length=20,
        choices=FormalityLevel.choices,
        default=FormalityLevel.BUSINESS,
        verbose_name=_('Уровень официальности')
    )

    # ===== ДОПОЛНИТЕЛЬНЫЕ УСЛОВИЯ =====

    requires_business_trip = BooleanField(
        default=False,
        verbose_name=_('Требуется командировка')
    )

    requires_hotel = BooleanField(
        default=False,
        verbose_name=_('Требуется отель')
    )

    gender_requirement = CharField(
        max_length=20,
        choices=GenderRequirement.choices,
        default=GenderRequirement.NO_PREFERENCE,
        verbose_name=_('Требования к полу переводчика')
    )

    # ===== ФИНАНСЫ =====

    client_budget = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Бюджет клиента'),
        help_text=_('В валюте USD')
    )

    interpreter_rate = DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Ставка переводчика')
    )

    # ===== СТАТУС =====

    status = CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
        verbose_name=_('Статус заказа'),
    )

    # ===== ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ =====

    notes = TextField(
        blank=True,
        verbose_name=_('Примечания'),
        help_text=_('Дополнительные пожелания клиента')
    )

    # ===== META =====

    class Meta:
        db_table = 'orders'
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-created_at']

    # ===== МЕТОДЫ =====

    def __str__(self):
        return f"Заказ #{str(self.id)[:8]} - {self.client} ({self.get_status_display()})"

    def clean(self):
        """Валидация бизнес-логики"""
        errors = {}

        if self.end_datetime and self.start_datetime:
            if self.end_datetime <= self.start_datetime:
                errors['end_datetime'] = 'Дата окончания должна быть позже даты начала'

        if self.location_type == self.LocationType.ONSITE and not self.city:
            errors['city'] = 'Для заказа в городе необходимо указать город'

        if self.location_type == self.LocationType.ONLINE:
            if not self.online_platform and not self.online_link:
                errors['online_platform'] = 'Для онлайн заказа укажите платформу или ссылку'

        if self.interpreter_count and self.interpreter_count < 1:
            errors['interpreter_count'] = 'Количество переводчиков должно быть минимум 1'

        if self.client_budget and self.client_budget < 0:
            errors['client_budget'] = 'Бюджет не может быть отрицательным'

        if self.interpreter_rate and self.interpreter_rate < 0:
            errors['interpreter_rate'] = 'Ставка не может быть отрицательной'

        if (self.interpreter_rate and self.client_budget and
                self.interpreter_rate > self.client_budget):
            errors['interpreter_rate'] = 'Ставка переводчика не может превышать бюджет клиента'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def duration_hours(self):
        """Длительность заказа в часах"""
        if self.start_datetime and self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return round(delta.total_seconds() / 3600, 2)
        return 0

    @property
    def is_online(self):
        """Проверка: онлайн заказ?"""
        return self.location_type == self.LocationType.ONLINE

    # @property
    # def platform_margin(self):
    #     """Маржа платформы (разница между бюджетом и ставкой)"""
    #     if self.interpreter_rate and self.client_budget:
    #         return self.client_budget - self.interpreter_rate
    #     return Decimal('0.00')

    def can_cancel(self):
        """Можно ли отменить заказ?"""
        return self.status in [
            self.OrderStatus.NEW,
            self.OrderStatus.SEARCHING
        ]

    def assign_interpreter(self, interpreter, rate):
        """Назначить переводчика на заказ"""
        if self.status not in [self.OrderStatus.NEW, self.OrderStatus.SEARCHING]:
            raise ValidationError('Можно назначить переводчика только на новый заказ или в поиске')

        self.interpreter_rate = rate
        self.status = self.OrderStatus.ASSIGNED
        self.save()

        # Создать связь с переводчиком (через промежуточную модель)
        OrderInterpreter.objects.create(
            order=self,
            interpreter=interpreter,
            rate=rate
        )


# ===== ПРОМЕЖУТОЧНАЯ МОДЕЛЬ ДЛЯ СВЯЗИ ЗАКАЗ-ПЕРЕВОДЧИК =====

class OrderInterpreter(UUIDBaseModel):
    """Связь заказа с переводчиками (для нескольких переводчиков)"""

    order = ForeignKey(
        'apps.Order',
        CASCADE,
        related_name='assigned_interpreters',
        verbose_name=_('Заказ')
    )

    interpreter = ForeignKey(
        'apps.Interpreter',
        CASCADE,
        related_name='assigned_orders',
        verbose_name=_('Переводчик')
    )

    rate = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Ставка переводчика')
    )

    assigned_at = DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата назначения')
    )

    class Meta:
        db_table = 'order_interpreters'
        verbose_name = _('Назначение переводчика')
        verbose_name_plural = _('Назначения переводчиков')
        unique_together = ['order', 'interpreter']  # Один переводчик не может быть назначен дважды

    def __str__(self):
        return f"{self.interpreter} → Заказ #{str(self.order.id)[:8]}"
