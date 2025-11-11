from django.contrib.auth.models import (AbstractUser, BaseUserManager,
                                        PermissionsMixin)
from django.core.validators import MinValueValidator
from django.db.models import (BooleanField, CharField, EmailField,
                              TextChoices, ManyToManyField, TextField, ForeignKey, SET_NULL, DecimalField)
from django.utils.translation import gettext_lazy as _

from apps.models.base import UUIDBaseModel, CreatedBaseModel


class UserManager(BaseUserManager):

    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError()
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email=email, password=password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class User(AbstractUser, PermissionsMixin, UUIDBaseModel):
    """Основная модель пользователя"""
    phone = CharField(_('Телефон'), max_length=9, blank=True)
    email = EmailField(unique=True)
    username = None
    is_verified = BooleanField(default=False)

    USERNAME_FIELD = 'email'  # Говорит используй поле emal для login вместо username
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Interpreter(User, CreatedBaseModel):
    """Основная модель переводчика"""

    class GenderType(TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'

    gender = CharField(_("Gender"), max_length=6, choices=GenderType.choices)
    is_ready_for_trips = BooleanField(default=False)
    is_moderated = BooleanField(_('Passed moderation'), default=False)

    # Relations
    language = ManyToManyField('apps.Language', verbose_name=_("Languages"))
    translation_type = ManyToManyField('apps.TranslationType', verbose_name=_("Translation Types"))
    city = ForeignKey('apps.City', SET_NULL, null=True, related_name="translators")

    class Meta:
        verbose_name = _('Переводчик')
        verbose_name_plural = _('Переводчики')


class Client(User):
    """Модель клиента"""

    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')

    def __str__(self):
        return self.email
