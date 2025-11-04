from apps.models.base import UUIDBaseModel
from django.db.models import CharField


class City(UUIDBaseModel):
    name = CharField(max_length=155, unique=True)
    country = CharField(max_length=155, blank=True)

    def __str__(self):
        return f"{self.name} ({self.country})" if self.country else self.name