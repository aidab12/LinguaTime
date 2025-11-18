from django.db.models import CASCADE, CharField, ForeignKey
from django.utils.translation import gettext_lazy as _

from apps.models.base import UUIDBaseModel


class Language(UUIDBaseModel):
    """Модель для языков"""
    name = CharField(max_length=100, unique=True)

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
    name = CharField(max_length=100, unique=True)
