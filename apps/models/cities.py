from apps.models.base import UUIDBaseModel
from django.db.models import CharField, ForeignKey, CASCADE


class Country(UUIDBaseModel):
    name = CharField(max_length=155, unique=True)

    def __str__(self):
        return self.name


class Region(UUIDBaseModel):
    name = CharField(max_length=155, unique=True)
    country = ForeignKey(Country, CASCADE, related_name='regions')

    def __str__(self):
        return self.name


class City(UUIDBaseModel):
    name = CharField(max_length=155)
    region = ForeignKey(Region, CASCADE, related_name='cities')

    class Meta:
        unique_together = ('name', 'region')

    def __str__(self):
        return f"{self.name}, {self.region.name}"
