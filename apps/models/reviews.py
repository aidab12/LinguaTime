from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import CASCADE, ForeignKey, PositiveSmallIntegerField, TextField

from apps.models.base import CreatedBaseModel


class Review(CreatedBaseModel):
    score = PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = TextField(blank=True)

    client = ForeignKey('apps.Client', CASCADE, related_name='reviews')
    interpreter = ForeignKey('apps.Interpreter', CASCADE, related_name='reviews')
