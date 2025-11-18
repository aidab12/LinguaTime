import os
import pickle
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings


class GoogleCalendarService:
    """Сервис для работы с Google Calendar API"""

    def __init__(self, user_id: str):
        """
        Args:
            user_id: ID пользователя (переводчика) для хранения токенов
        """
        self.user_id = user_id
        self.token_path = settings.GOOGLE_CALENDAR_TOKEN_DIR / f'token_{user_id}.pickle'
        self.creds = None
        self.service = None

    def get_credentials(self) -> Optional[Credentials]:
        """Получение или обновление credentials"""
        # Загружаем сохранённый токен
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)

        # Если токен истёк, обновляем его
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                self._save_credentials()
            except Exception as e:
                print(f"Error refreshing token: {e}")
                return None

        return self.creds

    def _save_credentials(self):
        """Сохранение credentials в файл"""
        with open(self.token_path, 'wb') as token:
            pickle.dump(self.creds, token)

    def save_credentials_from_flow(self, credentials: Credentials):
        """Сохранение credentials после OAuth flow"""
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
        Проверка доступности в указанный период

        Returns:
            True если свободен, False если занят
        """
        events = self.list_events(
            time_min=start_time,
            time_max=end_time,
            max_results=100
        )

        # Если есть события в этот период, значит занят
        return len(events) == 0

    def get_busy_times(self, start_time: datetime,
                       end_time: datetime) -> List[Dict]:
        """
        Получение списка занятых периодов

        Returns:
            List[Dict] с периодами {'start': datetime, 'end': datetime}
        """
        events = self.list_events(
            time_min=start_time,
            time_max=end_time,
            max_results=100
        )

        busy_times = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            busy_times.append({
                'start': datetime.fromisoformat(start.replace('Z', '+00:00')),
                'end': datetime.fromisoformat(end.replace('Z', '+00:00')),
                'summary': event.get('summary', 'Busy')
            })

        return busy_times