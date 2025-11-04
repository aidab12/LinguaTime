import os
import uuid
from datetime import datetime

from django.db.models import (CharField, DateTimeField, Func, ImageField,
                              Model, PositiveSmallIntegerField, SlugField,
                              TextChoices, URLField, UUIDField)
from django.utils.text import slugify

MAX_CHAR_LENGTH = 155


class GenRandomUUID(Func):
    """
    Represents the PostgreSQL gen_random_uuid() function.
    """
    function = "gen_random_uuid"
    template = "%(function)s()"  # no args
    output_field = UUIDField()


class UUIDBaseModel(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, db_default=GenRandomUUID(), editable=False)

    class Meta:
        abstract = True


class CreatedBaseModel(UUIDBaseModel):
    updated_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True




class SlugBasedModel(UUIDBaseModel):
    slug = SlugField(unique=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is None or not self.slug:
            source = getattr(self, 'name', None) or getattr(self, 'title', None)

            if source:
                self.slug = slugify(source, allow_unicode=True)

        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __str__(self):
        return self.slug


class SocialLinkBase(Model):
    class Platform(TextChoices):
        FACEBOOK = 'facebook', 'Facebook'
        INSTAGRAM = 'instagram', 'Instagram'
        YOUTUBE = 'youtube', 'YouTube'
        PINTEREST = 'pinterest', 'Pinterest'
        X = 'x', 'X'

    platform = CharField(
        max_length=20,
        choices=Platform.choices,
    )
    url = URLField(max_length=255)

    class Meta:
        abstract = True


class OrderNumberBaseModel(Model):
    order_number = PositiveSmallIntegerField(default=1)

    class Meta:
        abstract = True
