from django.db.models import ForeignKey, CASCADE, DecimalField

from apps.models.base import CreatedBaseModel


class TranslationRate(CreatedBaseModel):
    rate = DecimalField(max_digits=10, decimal_places=2)

    translator = ForeignKey('apps.Interpreter', CASCADE, related_name="rates")
    translation_type = ForeignKey('apps.TranslationType', CASCADE)

    class Meta:
        unique_together = ('translator', 'translation_type')
