from time import timezone

from django.db.models import(
    ForeignKey, CASCADE, TextChoices,
    DecimalField, CharField, DateTimeField)

from apps.models.base import CreatedBaseModel
from django.utils.translation import gettext_lazy as _

class Booking(CreatedBaseModel):
    """Модель для взаимодействия между заказом и переводчиком"""

    class Status(TextChoices):
        OFFERED = 'offered', _('Предложен')
        ACCEPTED = 'accepted', _('Принят')
        DECLINED = 'declined', _('Отклонен')
        COMPLETED = 'completed', _('Завершен')
        CANCELED = 'canceled', _('Отменен')


    order = ForeignKey(
        'apps.Order',
        CASCADE,
        related_name='bookings',
        verbose_name=_('Заказ')
    )

    interpreter = ForeignKey(
        'apps.Interpreter',
        CASCADE,
        related_name='bookings',
        verbose_name=_('Переводчик')
    )

    status = CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OFFERED,
        verbose_name=_('Статус')
    )

    offered_at = DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата предложения')
    )

    responded_at = DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата ответа')
    )

    actual_hours = DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Фактические часы')
    )

    payout = DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Сумма оплаты')
    )

    rate = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Ставка для переводчика')
    )

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
