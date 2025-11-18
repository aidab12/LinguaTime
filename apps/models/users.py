from django.contrib.auth.models import (AbstractUser, BaseUserManager,
                                        PermissionsMixin)
from django.core.validators import MinValueValidator
from django.db.models import (BooleanField, CharField, EmailField,
                              TextChoices, ManyToManyField, TextField, ForeignKey, SET_NULL, DecimalField)
from django.utils.translation import gettext_lazy as _

from apps.models.base import UUIDBaseModel, CreatedBaseModel

from apps.models.availabilitys import Availability
from datetime import datetime, timedelta

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
    google_calendar_connected = BooleanField(default=False) # New field

    # Relations
    language = ManyToManyField('apps.Language', verbose_name=_("Languages"))
    translation_type = ManyToManyField('apps.TranslationType', verbose_name=_("Translation Types"))
    city = ForeignKey('apps.City', SET_NULL, null=True, related_name="translators")

    class Meta:
        verbose_name = _('Interpreter')
        verbose_name_plural = _('Interpreters')

    def sync_availability_from_calendar(self):
        """
        Синхронизирует доступность переводчика из Google Calendar.
        """
        from apps.services.google_calendar import GoogleCalendarService
        if not self.google_calendar_connected:
            return

        calendar_service = GoogleCalendarService(str(self.id))
        if not calendar_service.is_authorized():
            # Если токен недействителен, помечаем как отключенный
            self.google_calendar_connected = False
            self.save(update_fields=['google_calendar_connected'])
            return

        # Определяем диапазон для синхронизации (например, на ближайшие 3 месяца)
        now = datetime.utcnow()
        time_min = now
        time_max = now + timedelta(days=90)

        busy_slots = calendar_service.get_user_availability(time_min, time_max)

        # Удаляем старые записи доступности, синхронизированные из Google Calendar
        Availability.objects.filter(interpreter=self, is_google_calendar_event=True).delete()

        # Создаем новые записи доступности на основе занятых слотов
        for slot in busy_slots:
            start = datetime.fromisoformat(slot['start'][:-1]) # Remove 'Z' for timezone-naive datetime
            end = datetime.fromisoformat(slot['end'][:-1]) # Remove 'Z' for timezone-naive datetime
            Availability.objects.create(
                interpreter=self,
                start_time=start,
                end_time=end,
                is_available=False, # Занято
                is_google_calendar_event=True
            )


class Client(User):
    """Модель клиента"""

    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')

    def __str__(self):
        return self.email
