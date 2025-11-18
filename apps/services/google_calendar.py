from datetime import datetime
from typing import Optional, List, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from apps.models import GoogleCalendarCredentials, Interpreter


class GoogleCalendarService:
    """Сервис для работы с Google Calendar API"""

    def __init__(self, user_id: str):
        """
        Args:
            user_id: ID пользователя (переводчика) для хранения токенов
        """
        self.user_id = user_id
        self.creds = None
        self.service = None

    def get_credentials(self) -> Optional[Credentials]:
        """Получение или обновление credentials из базы данных"""
        try:
            interpreter = Interpreter.objects.get(id=self.user_id)
            creds_db = interpreter.google_calendar_credentials
            
            self.creds = Credentials(
                token=creds_db.token,
                refresh_token=creds_db.refresh_token,
                token_uri=creds_db.token_uri,
                client_id=creds_db.client_id,
                client_secret=creds_db.client_secret,
                scopes=creds_db.scopes.split(' ')
            )

            # Если токен истёк, обновляем его
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    self._save_credentials() # Сохраняем обновленные токены в БД
                except Exception as e:
                    print(f"Error refreshing token for user {self.user_id}: {e}")
                    # Optionally, mark user as disconnected if refresh fails
                    interpreter.google_calendar_connected = False
                    interpreter.save(update_fields=['google_calendar_connected'])
                    return None
            
            return self.creds

        except GoogleCalendarCredentials.DoesNotExist:
            return None
        except Interpreter.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error loading credentials for user {self.user_id}: {e}")
            return None

    def _save_credentials(self):
        """Сохранение credentials в базу данных"""
        if not self.creds:
            return

        try:
            interpreter = Interpreter.objects.get(id=self.user_id)
            GoogleCalendarCredentials.objects.update_or_create(
                user=interpreter,
                defaults={
                    'token': self.creds.token,
                    'refresh_token': self.creds.refresh_token,
                    'token_uri': self.creds.token_uri,
                    'client_id': self.creds.client_id,
                    'client_secret': self.creds.client_secret,
                    'scopes': ' '.join(self.creds.scopes),
                }
            )
        except Interpreter.DoesNotExist:
            print(f"Interpreter with ID {self.user_id} not found for saving credentials.")
        except Exception as e:
            print(f"Error saving credentials for user {self.user_id}: {e}")

    def save_credentials_from_flow(self, credentials: Credentials):
        """Сохранение credentials после OAuth flow в базу данных"""
        self.creds = credentials
        self._save_credentials()

    def is_authorized(self) -> bool:
        """Проверка авторизации пользователя"""
        creds = self.get_credentials()
        return creds is not None and creds.valid

    def get_service(self):
        """Получение сервиса Calendar API"""
        if not self.service:
            creds = self.get_credentials()
            if not creds:
                raise ValueError("User not authorized with Google Calendar")

            self.service = build('calendar', 'v3', credentials=creds)
        return self.service

    # ============= CRUD операции для событий =============

    def create_event(self, summary: str, start_time: datetime,
                     end_time: datetime, description: str = "",
                     location: str = "") -> Dict:
        """
        Создание события в календаре

        Args:
            summary: Название события
            start_time: Время начала
            end_time: Время окончания
            description: Описание
            location: Локация

        Returns:
            Dict с данными созданного события
        """
        service = self.get_service()

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Tashkent',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Tashkent',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }

        try:
            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            return created_event
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise

    def get_event(self, event_id: str) -> Dict:
        """Получение события по ID"""
        service = self.get_service()

        try:
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return event
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise

    def update_event(self, event_id: str, **kwargs) -> Dict:
        """
        Обновление события

        Args:
            event_id: ID события
            **kwargs: Поля для обновления (summary, start_time, end_time, etc.)
        """
        service = self.get_service()

        # Получаем текущее событие
        event = self.get_event(event_id)

        # Обновляем поля
        if 'summary' in kwargs:
            event['summary'] = kwargs['summary']
        if 'description' in kwargs:
            event['description'] = kwargs['description']
        if 'location' in kwargs:
            event['location'] = kwargs['location']
        if 'start_time' in kwargs:
            event['start'] = {
                'dateTime': kwargs['start_time'].isoformat(),
                'timeZone': 'Asia/Tashkent',
            }
        if 'end_time' in kwargs:
            event['end'] = {
                'dateTime': kwargs['end_time'].isoformat(),
                'timeZone': 'Asia/Tashkent',
            }

        try:
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            return updated_event
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise

    def delete_event(self, event_id: str) -> bool:
        """Удаление события"""
        service = self.get_service()

        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True
        except HttpError as error:
            print(f'An error occurred: {error}')
            return False

    def list_events(self, max_results: int = 10,
                    time_min: Optional[datetime] = None,
                    time_max: Optional[datetime] = None) -> List[Dict]:
        """
        Получение списка событий

        Args:
            max_results: Максимальное количество событий
            time_min: Начало периода
            time_max: Конец периода
        """
        service = self.get_service()

        if not time_min:
            time_min = datetime.utcnow()

        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z' if time_max else None,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return events_result.get('items', [])
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def check_availability(self, start_time: datetime,
                           end_time: datetime) -> bool:
        """
        Проверка доступности в указанный период с использованием freebusy API.

        Returns:
            True если свободен, False если занят
        """
        service = self.get_service()

        body = {
            "timeMin": start_time.isoformat() + "Z",
            "timeMax": end_time.isoformat() + "Z",
            "items": [{"id": "primary"}]
        }

        try:
            events_result = service.freebusy().query(body=body).execute()
            # Если список busy пуст, значит свободен
            return not events_result['calendars']['primary']['busy']
        except HttpError as error:
            print(f'An error occurred while checking availability: {error}')
            raise

    def get_user_availability(self, time_min: datetime, time_max: datetime) -> List[Dict]:
        """
        Получение занятых слотов пользователя с использованием freebusy API.

        Args:
            time_min: Начало периода
            time_max: Конец периода

        Returns:
            List[Dict] с периодами {'start': str, 'end': str} в ISO формате
        """
        service = self.get_service()

        body = {
            "timeMin": time_min.isoformat() + "Z",
            "timeMax": time_max.isoformat() + "Z",
            "items": [{"id": "primary"}]  # Проверяем основной календарь
        }

        try:
            events_result = service.freebusy().query(body=body).execute()
            return events_result['calendars']['primary']['busy']
        except HttpError as error:
            print(f'An error occurred while fetching freebusy: {error}')
            raise