from apps.models.base import UUIDBaseModel
from django.db.models import CharField
from django.utils.translation import gettext_lazy as _

class Language(UUIDBaseModel):
    """Модель для языков"""
    name = CharField(max_length=100, unique=True, verbose_name=_("Название языка"))
    code = CharField(max_length=10, unique=True, verbose_name=_("Код языка (ISO 639)"))

    class Meta:
        verbose_name = _("Язык")
        verbose_name_plural = _("Языки")
        ordering = ['name']

    def __str__(self):
        return self.name