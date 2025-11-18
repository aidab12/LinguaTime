from django.core.exceptions import ValidationError
from django.db.models import (CASCADE, PROTECT, CharField, DateTimeField,
                              ForeignKey, ManyToManyField,
                              PositiveSmallIntegerField, TextChoices,
                              TextField)
from django.utils.translation import gettext_lazy as _

from apps.models.base import CreatedBaseModel, UUIDBaseModel


class Order(CreatedBaseModel):
    """Модель заказа на перевод"""

    # ===== CHOICES =====

    class LocationType(TextChoices):
        ONSITE = 'onsite', _('Onsite')
        ONLINE = 'online', _('Online')

    class FormalityLevel(TextChoices):
        BUSINESS = 'business', _('Business')
        OFFICIAL = 'official', _('Official')

    class GenderRequirement(TextChoices):
        NO_PREFERENCE = 'no_preference', _('no_preference')
        MALE = 'male', _('male')
        FEMALE = 'female', _('female')

    class OrderStatus(TextChoices):
        NEW = 'new', _('Новый')
        SEARCHING = 'searching', _('searching')
        ASSIGNED = 'assigned', _('assigned')
        COMPLETED = 'completed', _('completed')
        CANCELLED = 'cancelled', _('cancelled')

    # ===== ОСНОВНЫЕ ПОЛЯ =====

    client = ForeignKey('apps.Client', PROTECT, related_name='orders', verbose_name=_('Клиент'))

    # ===== ВРЕМЯ И ДАТА =====

    start_datetime = DateTimeField(_('Дата и время начала'))
    end_datetime = DateTimeField(_('Дата и время окончания'))

    # ===== ЛОКАЦИЯ =====

    location_type = CharField(_('Тип локации'), max_length=20, choices=LocationType.choices)

    city = ForeignKey('apps.City', PROTECT, blank=True, null=True, verbose_name=_('Город'),
                      help_text=_('Обязательно, если не онлайн')
                      )

    address = TextField()
    translation_types = ManyToManyField('apps.TranslationType', verbose_name=_("Translation Types"))
    interpreter_count = PositiveSmallIntegerField(default=1)
    languages = ManyToManyField('apps.Language', related_name='orders')
    formality_level = CharField(max_length=20, choices=FormalityLevel.choices, default=FormalityLevel.BUSINESS)
    status = CharField(_('Статус заказа'), max_length=20, choices=OrderStatus.choices, default=OrderStatus.NEW)
    notes = TextField(blank=True)

    class Meta:
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

        if self.interpreter_count and self.interpreter_count < 1:
            errors['interpreter_count'] = 'Количество переводчиков должно быть минимум 1'

        # if self.client_budget and self.client_budget < 0:
        #     errors['client_budget'] = 'Бюджет не может быть отрицательным'

        # if self.interpreter_rate and self.interpreter_rate < 0:
        #     errors['interpreter_rate'] = 'Ставка не может быть отрицательной'

        # if (self.interpreter_rate and self.client_budget and
        #         self.interpreter_rate > self.client_budget):
        #     errors['interpreter_rate'] = 'Ставка переводчика не может превышать бюджет клиента'

        if errors:
            raise ValidationError(errors)

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

    def can_cancel(self):
        """Можно ли отменить заказ?"""
        return self.status in [
            self.OrderStatus.NEW,
            self.OrderStatus.SEARCHING
        ]

    def assign_interpreter(self, interpreter):
        """Назначить переводчика на заказ"""
        if self.status not in [self.OrderStatus.NEW, self.OrderStatus.SEARCHING]:
            raise ValidationError('Можно назначить переводчика только на новый заказ или в поиске')

        # self.interpreter_rate = rate
        self.status = self.OrderStatus.ASSIGNED
        self.save()

        # Создать связь с переводчиком (через промежуточную модель)
        OrderInterpreter.objects.create(order=self, interpreter=interpreter)


# ===== ПРОМЕЖУТОЧНАЯ МОДЕЛЬ ДЛЯ СВЯЗИ ЗАКАЗ-ПЕРЕВОДЧИК =====

class OrderInterpreter(UUIDBaseModel):
    """Связь заказа с переводчиками (для нескольких переводчиков)"""

    order = ForeignKey('apps.Order', CASCADE, related_name='assigned_interpreters', verbose_name=_('Заказ'))

    interpreter = ForeignKey('apps.Interpreter', CASCADE, related_name='assigned_orders', verbose_name=_('Переводчик'))

    # rate = DecimalField(
    #     max_digits=10,
    #     decimal_places=2,
    #     verbose_name=_('Ставка переводчика')
    # )

    assigned_at = DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_interpreters'
        verbose_name = _('Назначение переводчика')
        verbose_name_plural = _('Назначения переводчиков')
        unique_together = ['order', 'interpreter']  # Один переводчик не может быть назначен дважды

    def __str__(self):
        return f"{self.interpreter} → Заказ #{str(self.order.id)[:8]}"
