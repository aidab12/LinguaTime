from django.db.models import BooleanField, DateTimeField, ForeignKey, CASCADE, OneToOneField
from django.db.models.fields import CharField, TextField
from django.utils.translation import gettext_lazy as _

from apps.models.base import CreatedBaseModel


class GoogleCalendarWebhookChannel(CreatedBaseModel):
    """Модель для отслеживания Google Calendar webhook каналов"""

    channel_id = CharField(_('ID канала'), max_length=255, unique=True, help_text=_('UUID канала от Google'))
    resource_id = CharField(_('ID ресурса'), max_length=255, help_text=_('ID ресурса от Google'))
    resource_uri = TextField(_('URI ресурса'), help_text=_('URI ресурса от Google'))
    expiration = DateTimeField(_('Время истечения'), null=True, blank=True,
                               help_text=_('Когда канал истечет (максимум 7 дней)'))
    is_active = BooleanField(_('Активен'), default=True, help_text=_('Активен ли канал'))

    interpreter = ForeignKey('apps.Interpreter', CASCADE, related_name='calendar_channels',
                             verbose_name=_('Переводчик'))

    class Meta:
        verbose_name = _('Google Calendar Webhook канал')
        verbose_name_plural = _('Google Calendar Webhook каналы')
        ordering = ['-created_at']

    def __str__(self):
        return f"Канал {self.channel_id[:8]} для {self.interpreter}"


class GoogleCalendarCredentials(CreatedBaseModel):
    user = OneToOneField('apps.Interpreter', CASCADE, related_name='google_calendar_credentials')
    token = CharField(max_length=255)
    refresh_token = CharField(max_length=255, null=True, blank=True)
    token_uri = CharField(max_length=255)
    client_id = CharField(max_length=255)
    client_secret = CharField(max_length=255)
    scopes = TextField()

    def __str__(self):
        return f"Credentials for {self.user.email}"
