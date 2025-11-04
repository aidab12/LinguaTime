from apps.models.base import UUIDBaseModel
from django.db.models import CharField


class Specialization(UUIDBaseModel):
    name = CharField(max_length=155, unique=True)

    def __str__(self):
        return self.name