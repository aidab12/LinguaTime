import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from apps.models import (Availability, GoogleCalendarCredentials,
                         GoogleCalendarWebhookChannel, Interpreter)

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """
    Сервис для интеграции с Google Calendar

    Основные возможности:
    - Авторизация пользователей через OAuth2
    - Настройка webhook каналов для push notifications
    - Чтение событий из календаря
    - Синхронизация доступности переводчиков
    """

    SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events.readonly'
    ]

    def __init__(self, interpreter: Interpreter):
        """
        Args:
            interpreter: Экземпляр модели Interpreter (User object)
        """
        self.interpreter = interpreter
        self.service = None

    def is_authorized(self) -> bool:
        """
        Проверить существование и валидность учетных данных

        Returns:
            bool: True если учетные данные существуют и валидны
        """
        try:
            credentials = GoogleCalendarCredentials.objects.filter(
                user=self.interpreter
            ).first()

            if not credentials:
                return False

            # Проверить валидность токена
            creds = self._credentials_from_model(credentials)
            return creds and (creds.valid or creds.refresh_token)
        except Exception as e:
            logger.error(f"Error checking authorization for {self.interpreter.id}: {e}")
            return False

    def get_credentials(self) -> Optional[Credentials]:
        """
        Загрузить учетные данные из БД и обновить при необходимости

        Returns:
            Credentials или None если не найдены
        """
        try:
            credentials_model = GoogleCalendarCredentials.objects.filter(
                user=self.interpreter
            ).first()

            if not credentials_model:
                logger.warning(f"No credentials found for interpreter {self.interpreter.id}")
                return None

            creds = self._credentials_from_model(credentials_model)

            # Обновить если истекли
            if creds and creds.expired and creds.refresh_token:
                creds = self.refresh_credentials(creds, credentials_model)

            return creds
        except Exception as e:
            logger.error(f"Error getting credentials for {self.interpreter.id}: {e}")
            return None

    def get_service(self):
        """
        Получить или создать Google Calendar API service

        Returns:
            Resource: Google Calendar API service
        """
        if self.service:
            return self.service

        creds = self.get_credentials()
        if not creds:
            raise ValueError("No valid credentials available")

        self.service = build('calendar', 'v3', credentials=creds)
        return self.service

    def setup_watch_channel(self, calendar_id: str = 'primary') -> Optional[GoogleCalendarWebhookChannel]:
        """
        Создать webhook канал для получения уведомлений о изменениях календаря

        Args:
            calendar_id: ID календаря (по умолчанию 'primary')

        Returns:
            GoogleCalendarWebhookChannel или None при ошибке
        """
        try:
            service = self.get_service()

            # Генерировать уникальный ID канала
            channel_id = str(uuid.uuid4())

            # Webhook URL
            webhook_url = f"{settings.WEBHOOK_URL_BASE}/webhook/google-calendar/"

            # Время истечения (максимум 7 дней)
            expiration = int((timezone.now() + timedelta(days=7)).timestamp() * 1000)

            # Создать watch request
            request_body = {
                'id': channel_id,
                'type': 'web_hook',
                'address': webhook_url,
                'token': str(self.interpreter.id),  # ID переводчика для идентификации
                'expiration': expiration
            }

            # Отправить запрос
            response = service.events().watch(
                calendarId=calendar_id,
                body=request_body
            ).execute()

            # Сохранить в БД
            channel = GoogleCalendarWebhookChannel.objects.create(
                interpreter=self.interpreter,
                channel_id=response['id'],
                resource_id=response['resourceId'],
                resource_uri=response['resourceUri'],
                expiration=datetime.fromtimestamp(int(response['expiration']) / 1000, tz=timezone.utc)
            )

            logger.info(f"Created webhook channel {channel_id} for interpreter {self.interpreter.id}")
            return channel

        except HttpError as e:
            logger.error(f"HTTP error creating webhook channel: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating webhook channel for {self.interpreter.id}: {e}")
            return None

    def stop_watch_channel(self, channel: GoogleCalendarWebhookChannel) -> bool:
        """
        Остановить webhook канал

        Args:
            channel: Экземпляр GoogleCalendarWebhookChannel

        Returns:
            bool: True если успешно остановлен
        """
        try:
            service = self.get_service()

            # Остановить канал
            service.channels().stop(body={
                'id': channel.channel_id,
                'resourceId': channel.resource_id
            }).execute()

            # Обновить статус в БД
            channel.is_active = False
            channel.save()

            logger.info(f"Stopped webhook channel {channel.channel_id}")
            return True

        except HttpError as e:
            logger.error(f"HTTP error stopping webhook channel: {e}")
            return False
        except Exception as e:
            logger.error(f"Error stopping webhook channel {channel.channel_id}: {e}")
            return False

    def fetch_calendar_events(
        self,
        calendar_id: str = 'primary',
        time_min: Optional[datetime] = None,
        sync_token: Optional[str] = None
    ) -> dict:
        """
        Получить события из Google Calendar API

        Args:
            calendar_id: ID календаря
            time_min: Минимальное время для первой синхронизации
            sync_token: Токен для инкрементальной синхронизации

        Returns:
            dict с ключами 'events', 'next_sync_token', 'next_page_token'
        """
        try:
            service = self.get_service()

            # Параметры запроса
            params = {
                'calendarId': calendar_id,
                'singleEvents': True,
                'orderBy': 'startTime'
            }

            if sync_token:
                # Инкрементальная синхронизация
                params['syncToken'] = sync_token
            else:
                # Полная синхронизация
                if not time_min:
                    time_min = timezone.now()
                params['timeMin'] = time_min.isoformat()

            # Получить события
            events_result = service.events().list(**params).execute()

            return {
                'events': events_result.get('items', []),
                'next_sync_token': events_result.get('nextSyncToken'),
                'next_page_token': events_result.get('nextPageToken')
            }

        except HttpError as e:
            if e.resp.status == 410:
                # Sync token невалиден - нужна полная синхронизация
                logger.warning(f"Sync token invalid for {self.interpreter.id}, full sync required")
                # Очистить локальные события
                Availability.objects.filter(
                    translator=self.interpreter,
                    is_google_calendar_event=True
                ).delete()

                # Повторить без sync token
                return self.fetch_calendar_events(calendar_id=calendar_id, time_min=time_min)
            else:
                logger.error(f"HTTP error fetching events: {e}")
                raise
        except Exception as e:
            logger.error(f"Error fetching calendar events for {self.interpreter.id}: {e}")
            raise

    def sync_events_to_availability(self, events: list) -> int:
        """
        Сохранить события календаря в модель Availability

        Args:
            events: Список событий из Google Calendar

        Returns:
            int: Количество синхронизированных событий
        """
        synced_count = 0

        for event in events:
            try:
                # Пропустить события без времени
                if 'start' not in event or 'end' not in event:
                    continue

                # Получить время начала и конца
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))

                if not start or not end:
                    continue

                # Преобразовать в datetime
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))

                # Создать или обновить Availability
                Availability.objects.update_or_create(
                    translator=self.interpreter,
                    google_event_id=event['id'],
                    defaults={
                        'start_datetime': start_dt,
                        'end_datetime': end_dt,
                        'type': 'BUSY',
                        'is_google_calendar_event': True,
                        'last_synced_at': timezone.now()
                    }
                )

                synced_count += 1

            except Exception as e:
                logger.error(f"Error syncing event {event.get('id')}: {e}")
                continue

        return synced_count

    def refresh_credentials(
        self,
        credentials: Credentials,
        credentials_model: GoogleCalendarCredentials
    ) -> Credentials:
        """
        Обновить истекшие access tokens

        Args:
            credentials: Credentials объект
            credentials_model: Модель GoogleCalendarCredentials

        Returns:
            Credentials: Обновленные credentials
        """
        try:
            credentials.refresh(Request())

            # Сохранить обновленные токены
            credentials_model.token = credentials.token
            if credentials.refresh_token:
                credentials_model.refresh_token = credentials.refresh_token
            credentials_model.save()

            logger.info(f"Refreshed credentials for interpreter {self.interpreter.id}")
            return credentials

        except Exception as e:
            logger.error(f"Error refreshing credentials for {self.interpreter.id}: {e}")
            raise

    def sync_calendar(self) -> dict:
        """
        Главный метод синхронизации (оркестратор)

        Returns:
            dict: Статистика синхронизации
        """
        try:
            # Получить последний sync token
            last_availability = Availability.objects.filter(
                translator=self.interpreter,
                is_google_calendar_event=True,
                google_sync_token__isnull=False
            ).order_by('-last_synced_at').first()

            sync_token = last_availability.google_sync_token if last_availability else None

            # Получить события
            result = self.fetch_calendar_events(sync_token=sync_token)

            # Синхронизировать события
            synced_count = self.sync_events_to_availability(result['events'])

            # Сохранить новый sync token
            if result['next_sync_token']:
                # Обновить все события с новым sync token
                Availability.objects.filter(
                    translator=self.interpreter,
                    is_google_calendar_event=True
                ).update(google_sync_token=result['next_sync_token'])

            # Обновить last_calendar_sync у переводчика
            self.interpreter.last_calendar_sync = timezone.now()
            self.interpreter.save(update_fields=['last_calendar_sync'])

            logger.info(f"Synced {synced_count} events for interpreter {self.interpreter.id}")

            return {
                'success': True,
                'synced_count': synced_count,
                'sync_token': result['next_sync_token']
            }

        except Exception as e:
            logger.error(f"Error syncing calendar for {self.interpreter.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _credentials_from_model(self, credentials_model: GoogleCalendarCredentials) -> Optional[Credentials]:
        """
        Создать Credentials объект из модели

        Args:
            credentials_model: Модель GoogleCalendarCredentials

        Returns:
            Credentials или None
        """
        try:
            return Credentials(
                token=credentials_model.token,
                refresh_token=credentials_model.refresh_token,
                token_uri=credentials_model.token_uri,
                client_id=credentials_model.client_id,
                client_secret=credentials_model.client_secret,
                scopes=credentials_model.scopes
            )
        except Exception as e:
            logger.error(f"Error creating credentials from model: {e}")
            return None
