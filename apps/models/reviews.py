from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import CASCADE, ForeignKey, PositiveSmallIntegerField, TextField
from django.utils.translation import gettext_lazy as _
from apps.models.base import CreatedBaseModel


class Review(CreatedBaseModel):
    score = PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = TextField(blank=True)

    client = ForeignKey('apps.Client', CASCADE, related_name='reviews')
    interpreter = ForeignKey('apps.Interpreter', CASCADE, related_name='reviews')

    class Meta:
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')
        ordering = ['-created_at']