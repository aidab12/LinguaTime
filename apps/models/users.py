from django.contrib.auth.models import (AbstractUser, BaseUserManager,
                                        PermissionsMixin)
from django.db.models import (SET_NULL, BooleanField, CharField, DateTimeField,
                              EmailField, ForeignKey, JSONField,
                              ManyToManyField, TextChoices)
from django.utils.translation import gettext_lazy as _

from apps.models.base import CreatedBaseModel, UUIDBaseModel

NULLABLE = {'blank': True, 'null': True}


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

    class UserType(TextChoices):
        INTERPRETER = 'interpreter', _('Interpreter')
        CLIENT = 'client', _('Client')
        BOTH = 'both', _('Both')

    phone = CharField(_('Телефон'), max_length=9, blank=True)
    email = EmailField(unique=True)
    username = None
    is_verified = BooleanField(default=False)

    # Роль пользователя: переводчик, клиент или оба
    user_type = CharField(_('User Type'), max_length=20, choices=UserType.choices, default=UserType.CLIENT)

    # Текущая активная роль (используется когда user_type = BOTH)
    current_role = CharField(_('Current Role'), max_length=20, choices=UserType.choices, default=UserType.CLIENT,
                             help_text=_('Текущая активная роль пользователя')
                             )

    USERNAME_FIELD = 'email'  # Говорит используй поле emal для login вместо username
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_interpreter(self):
        """Проверяет, является ли пользователь переводчиком в текущей роли"""
        return self.current_role == self.UserType.INTERPRETER

    @property
    def is_client(self):
        """Проверяет, является ли пользователь клиентом в текущей роли"""
        return self.current_role == self.UserType.CLIENT

    def can_be_interpreter(self):
        """Проверяет, может ли пользователь работать как переводчик"""
        return self.user_type in [self.UserType.INTERPRETER, self.UserType.BOTH]

    def can_be_client(self):
        """Проверяет, может ли пользователь работать как клиент"""
        return self.user_type in [self.UserType.CLIENT, self.UserType.BOTH]

    def switch_role(self, new_role):
        """
        Переключает текущую роль пользователя

        Args:
            new_role: Новая роль (UserType.INTERPRETER или UserType.CLIENT)

        Returns:
            bool: True если переключение успешно, False если роль недоступна
        """
        if new_role == self.UserType.INTERPRETER and self.can_be_interpreter():
            self.current_role = self.UserType.INTERPRETER
            self.save(update_fields=['current_role'])
            return True
        elif new_role == self.UserType.CLIENT and self.can_be_client():
            self.current_role = self.UserType.CLIENT
            self.save(update_fields=['current_role'])
            return True
        return False


class Interpreter(User, CreatedBaseModel):
    """Основная модель переводчика"""

    class GenderType(TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'

    gender = CharField(_("Gender"), max_length=6, choices=GenderType.choices, blank=True, null=True)
    is_ready_for_trips = BooleanField(default=False)
    is_moderated = BooleanField(_('Passed moderation'), default=False)

    # Google Calendar Integration Fields
    google_calendar_connected = BooleanField(_('Google Calendar подключен'), default=False,
                                             help_text=_('Включена ли синхронизация с Google Calendar')
                                             )
    google_credentials = JSONField(_('Google учетные данные'), **NULLABLE,
                                   help_text=_('Зашифрованные токены доступа к Google Calendar')
                                   )
    google_calendar_id = CharField(_('ID календаря Google'), max_length=255, **NULLABLE, default='primary',
                                   help_text=_('ID календаря для синхронизации (по умолчанию: основной календарь)')
                                   )
    last_calendar_sync = DateTimeField(_('Последняя синхронизация календаря'), **NULLABLE)

    # Telegram Integration Fields
    telegram_chat_id = CharField(_('Telegram Chat ID'), max_length=255, null=True, blank=True)
    telegram_username = CharField(_('Telegram Username'), max_length=255, null=True, blank=True)

    # Relations
    language = ManyToManyField('apps.Language', verbose_name=_("Languages"))
    translation_type = ManyToManyField('apps.TranslationType', verbose_name=_("Translation Types"))
    city = ForeignKey('apps.City', SET_NULL, null=True, related_name="translators")

    class Meta:
        verbose_name = _('Interpreter')
        verbose_name_plural = _('Interpreters')

    def has_google_calendar(self):
        """Проверяет, подключен ли Google Calendar"""
        return self.google_calendar_connected and self.google_credentials is not None

    def sync_availability_from_calendar(self):
        """Синхронизирует доступность из событий Google Calendar"""
        from apps.services.google_calendar import GoogleCalendarService

        service = GoogleCalendarService(self)
        return service.sync_calendar()


class Client(User):
    """Модель клиента"""

    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')
