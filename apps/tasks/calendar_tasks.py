"""
Celery tasks для Google Calendar интеграции
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def renew_expiring_channels():
    """
    Периодическая задача для обновления каналов истекающих в течение 24 часов

    Запускается ежедневно через Celery Beat
    """
    from apps.models import GoogleCalendarWebhookChannel
    from apps.services.google_calendar import GoogleCalendarService

    # Найти каналы истекающие в течение 24 часов
    tomorrow = timezone.now() + timedelta(hours=24)
    expiring_channels = GoogleCalendarWebhookChannel.objects.filter(
        is_active=True,
        expiration__lte=tomorrow
    )

    renewed_count = 0
    for channel in expiring_channels:
        try:
            service = GoogleCalendarService(channel.interpreter)

            # Остановить старый канал
            service.stop_watch_channel(channel)

            # Создать новый канал
            new_channel = service.setup_watch_channel()

            if new_channel:
                renewed_count += 1
                logger.info(f"Renewed channel for interpreter {channel.interpreter.id}")

        except Exception as e:
            logger.error(f"Error renewing channel {channel.id}: {e}")
            continue

    logger.info(f"Renewed {renewed_count} expiring channels")
    return {'renewed_count': renewed_count}


@shared_task
def sync_interpreter_calendar(interpreter_id: str):
    """
    Асинхронная задача для синхронизации календаря конкретного переводчика

    Args:
        interpreter_id: ID переводчика
    """
    from apps.models import Interpreter
    from apps.services.google_calendar import GoogleCalendarService

    try:
        interpreter = Interpreter.objects.get(id=interpreter_id)
        service = GoogleCalendarService(interpreter)

        result = service.sync_calendar()

        if result['success']:
            logger.info(f"Synced {result['synced_count']} events for interpreter {interpreter_id}")
        else:
            logger.error(f"Sync failed for interpreter {interpreter_id}: {result.get('error')}")

        return result

    except Interpreter.DoesNotExist:
        logger.error(f"Interpreter {interpreter_id} not found")
        return {'success': False, 'error': 'Interpreter not found'}
    except Exception as e:
        logger.error(f"Error syncing calendar for interpreter {interpreter_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def setup_watch_for_interpreter(interpreter_id: str):
    """
    Асинхронная задача для настройки webhook канала для переводчика

    Args:
        interpreter_id: ID переводчика
    """
    from apps.models import Interpreter
    from apps.services.google_calendar import GoogleCalendarService

    try:
        interpreter = Interpreter.objects.get(id=interpreter_id)
        service = GoogleCalendarService(interpreter)

        channel = service.setup_watch_channel()

        if channel:
            logger.info(f"Setup watch channel for interpreter {interpreter_id}")
            return {'success': True, 'channel_id': str(channel.id)}
        else:
            logger.error(f"Failed to setup watch channel for interpreter {interpreter_id}")
            return {'success': False, 'error': 'Failed to create channel'}

    except Interpreter.DoesNotExist:
        logger.error(f"Interpreter {interpreter_id} not found")
        return {'success': False, 'error': 'Interpreter not found'}
    except Exception as e:
        logger.error(f"Error setting up watch for interpreter {interpreter_id}: {e}")
        return {'success': False, 'error': str(e)}
