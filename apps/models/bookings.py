from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import CASCADE, ForeignKey, PositiveSmallIntegerField, TextField, TextChoices, DecimalField, \
    CharField, DateTimeField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.models.base import CreatedBaseModel


class Booking(CreatedBaseModel):
    """Модель для взаимодействия между заказом и переводчиком"""

    class Status(TextChoices):
        OFFERED = 'offered', _('Предложен')
        ACCEPTED = 'accepted', _('Принят')
        DECLINED = 'declined', _('Отклонен')
        COMPLETED = 'completed', _('Завершен')
        CANCELED = 'canceled', _('Отменен')

    order = ForeignKey('apps.Order', CASCADE, related_name='bookings', verbose_name=_('Заказ'))
    interpreter = ForeignKey('apps.Interpreter', CASCADE, related_name='bookings', verbose_name=_('Переводчик'))
    status = CharField(_('Статус'), max_length=20, choices=Status.choices, default=Status.OFFERED)
    offered_at = DateTimeField(_('Дата предложения'), auto_now_add=True)
    responded_at = DateTimeField(_('Дата ответа'), null=True, blank=True)
    actual_hours = DecimalField(_('Фактические часы'), max_digits=5, decimal_places=2, null=True, blank=True)
    payout = DecimalField(_('Сумма оплаты'), max_digits=10, decimal_places=2, null=True, blank=True)
    rate = DecimalField(_('Ставка для переводчика'), max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'bookings'
        verbose_name = _('Бронирование')
        verbose_name_plural = _('Бронирования')
        unique_together = ['order', 'interpreter']  # чтобы не было дубликатов предложений

    def __str__(self):
        return f"{self.interpreter} — {self.order} ({self.get_status_display()})"

    def accept(self):
        """Принятие предложения переводчиком"""
        self.status = self.Status.ACCEPTED
        self.responded_at = timezone.now()
        self.save()

        # создаем запись о назначении переводчика
        from apps.models import OrderInterpreter
        OrderInterpreter.objects.get_or_create(
            order=self.order,
            interpreter=self.interpreter,
            defaults={'rate': self.rate}
        )

    def decline(self):
        """Отклонение предложения переводчиком"""
        self.status = self.Status.DECLINED
        self.responded_at = timezone.now()
        self.save()


class Review(CreatedBaseModel):
    score = PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = TextField(blank=True)

    client = ForeignKey('apps.Client', CASCADE, related_name='reviews')
    interpreter = ForeignKey('apps.Interpreter', CASCADE, related_name='reviews')

    class Meta:
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')
        ordering = ['-created_at']
