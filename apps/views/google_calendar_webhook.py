"""
Google Calendar Webhook View для обработки push notifications
"""
import logging

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleCalendarWebhookView(View):
    """
    Class-based view для обработки Google Calendar Push Notifications

    Заголовки (Headers) от Google:
    - X-Goog-Channel-ID: Идентификатор канала (UUID)
    - X-Goog-Resource-ID: Идентификатор ресурса (из response при создании watch)
    - X-Goog-Resource-State: Состояние ресурса
      * 'sync' - Первое уведомление при создании канала (подтверждение)
      * 'exists' - Ресурс изменился (нужно получить изменения)
      * 'not_exists' - Ресурс удален
      * 'stop' - Канал остановлен
    - X-Goog-Resource-URI: URI ресурса
    - X-Goog-Channel-Token: Токен канала (наш interpreter_id)
    - X-Goog-Channel-Expiration: Время истечения канала (RFC 3339)
    - X-Goog-Message-Number: Порядковый номер сообщения

    ВАЖНО: Тело запроса (body) пустое! Вся информация в заголовках.
    """

    def post(self, request):
        """Обработка POST запроса от Google"""
        # Извлечение заголовков
        channel_id = request.headers.get('X-Goog-Channel-ID')
        # resource_id = request.headers.get('X-Goog-Resource-ID')
        resource_state = request.headers.get('X-Goog-Resource-State')
        channel_token = request.headers.get('X-Goog-Channel-Token')

        logger.info(f"Webhook received: channel={channel_id}, state={resource_state}")

        # Обработка различных состояний
        if resource_state == 'sync':
            self._handle_sync(channel_id, channel_token)
        elif resource_state == 'exists':
            self._handle_exists(channel_token)
        elif resource_state == 'stop':
            self._handle_stop(channel_id)

        return HttpResponse(status=200)

    def _handle_sync(self, channel_id, channel_token):
        """Обработка sync события (подтверждение создания канала)"""
        logger.info(f"Channel {channel_id} established for interpreter {channel_token}")

    def _handle_exists(self, channel_token):
        """Обработка exists события (календарь изменился)"""
        from apps.tasks.calendar_tasks import sync_interpreter_calendar

        if channel_token:
            # Запустить асинхронную задачу синхронизации
            sync_interpreter_calendar.delay(channel_token)
            logger.info(f"Sync task queued for interpreter {channel_token}")

    def _handle_stop(self, channel_id):
        """Обработка stop события (канал остановлен)"""
        from apps.models import GoogleCalendarWebhookChannel

        GoogleCalendarWebhookChannel.objects.filter(
            channel_id=channel_id
        ).update(is_active=False)
        logger.info(f"Channel {channel_id} marked as inactive")
