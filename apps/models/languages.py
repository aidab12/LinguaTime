from django.db.models import CharField
from django.utils.translation import gettext_lazy as _

from apps.models.base import UUIDBaseModel


class Language(UUIDBaseModel):
    """Модель для языков"""
    name = CharField(max_length=100, unique=True)


    class Meta:
        verbose_name = _("Язык")
        verbose_name_plural = _("Языки")
        ordering = ['name']

    def __str__(self):
        return self.name

class TranslationType(UUIDBaseModel):
    name = CharField(max_length=100, unique=True)