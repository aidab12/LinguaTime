from django.contrib.auth.models import (AbstractUser, BaseUserManager,
                                        PermissionsMixin)
from django.core.validators import MinValueValidator
from django.db.models import (BooleanField, CharField, DateField, EmailField,
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

    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')
        unique_together = ('email',)

    def __str__(self):
        return self.email


class Interpreter(User, CreatedBaseModel):
    """Основная модель переводчика"""

    class GenderType(TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'

    class LangLevel(TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
        NATIVE = 'native', 'Native'

    gender = CharField(
        max_length=6,
        choices=GenderType.choices,  # type: ignore
        verbose_name=_("Пол")
    )
    language = ManyToManyField('apps.Language')
    language_level = CharField(
        max_length=20,
        choices=LangLevel.choices,  # type: ignore
        default=LangLevel.BEGINNER
    )
    translation_type = ManyToManyField('apps.TranslationType')
    experience = TextField()
    is_ready_for_trips = BooleanField(default=False)
    city = ForeignKey('apps.City', SET_NULL, null=True, related_name="translators")
    specializations = ManyToManyField('apps.Specialization', related_name='translators')
    hourly_rate = DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )


class Client(User):
    """Модель клиента (физическое или юридическое лицо)"""

    class ClientType(TextChoices):
        INDIVIDUAL = 'individual', _('Физическое лицо')
        LEGAL = 'legal', _('Юридическое лицо')

    client_type = CharField(
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.INDIVIDUAL,
        verbose_name='Тип клиента',
        db_index=True  # Индекс для быстрой фильтрации
    )

    # Поля для юридического лица

    company_name = CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Название компании')
    )

    tax_id = CharField(_('ИНН'), max_length=50, blank=True, unique=True, null=True)
    legal_address = TextField(_('Юридический адрес'), blank=True)

    # Метаданные
    is_active = BooleanField(_('Активен'), default=False)

    class Meta:
        db_table = 'clients'
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']

    def __str__(self):
        if self.client_type == self.ClientType.INDIVIDUAL:
            return f"{self.first_name} {self.last_name}".strip() or self.email
        else:
            return self.company_name or self.email

    def clean(self):
        """Валидация в зависимости от типа клиента"""
        from django.core.exceptions import ValidationError

        if self.client_type == self.ClientType.INDIVIDUAL:
            if not self.first_name or not self.last_name:
                raise ValidationError({
                    'first_name': 'Для физического лица обязательно имя',
                    'last_name': 'Для физического лица обязательна фамилия'
                })

        elif self.client_type == self.ClientType.LEGAL:
            if not self.company_name:
                raise ValidationError({
                    'company_name': 'Для юридического лица обязательно название компании'
                })
            if not self.tax_id:
                raise ValidationError({
                    'tax_id': 'Для юридического лица обязателен ИНН/Tax ID'
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        """Удобное отображение имени клиента"""
        if self.client_type == self.ClientType.INDIVIDUAL:
            return f"{self.first_name} {self.last_name}"
        return self.company_name
