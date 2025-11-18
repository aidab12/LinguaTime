import logging
import secrets
import urllib.parse

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View

from apps.models import (  # Import GoogleCalendarCredentials
    GoogleCalendarCredentials, Interpreter)
from apps.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)


class GoogleCalendarAuthorizeView(LoginRequiredMixin, View):
    """
    Инициирует OAuth flow для подключения Google Calendar.
    Только для авторизованных переводчиков.
    """

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"

    def get(self, request):
        """Инициирует Calendar OAuth flow"""

        # Проверяем, что пользователь - переводчик
        if not isinstance(request.user, Interpreter):
            messages.error(request, "Only interpreters can connect Google Calendar")
            return redirect('interpreter_profile')

        # Проверяем, не подключён ли уже календарь
        if request.user.google_calendar_connected:
            # Use the service to check if credentials are still valid
            calendar_service = GoogleCalendarService(str(request.user.id))
            if calendar_service.is_authorized():
                messages.info(request, "Calendar is already connected and authorized.")
                return redirect('interpreter_profile')
            else:
                # If not authorized, reset connection status to allow re-authorization
                request.user.google_calendar_connected = False
                request.user.save(update_fields=['google_calendar_connected'])
                messages.warning(request, "Your Google Calendar connection needs to be re-authorized.")

        # Генерируем state для CSRF защиты
        state = secrets.token_urlsafe(32)
        request.session['google_calendar_state'] = state
        request.session['google_calendar_user_id'] = str(request.user.id)

        # Строим authorization URL
        auth_url = self._build_auth_url(state)

        logger.info(f"Initiating Calendar OAuth for user {request.user.email}")

        return redirect(auth_url)

    def _build_auth_url(self, state):
        """Создаёт URL для Google Calendar OAuth"""

        calendar_scopes = settings.GOOGLE_OAUTH_SCOPES['calendar']

        params = {
            'response_type': 'code',
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_CALENDAR_REDIRECT_URI,
            'scope': ' '.join(calendar_scopes),
            'state': state,
            'access_type': 'offline',  # ВАЖНО: для получения refresh_token
            'prompt': 'consent',  # ВАЖНО: всегда запрашиваем согласие
        }

        query_string = urllib.parse.urlencode(params)
        return f"{self.GOOGLE_AUTH_URL}?{query_string}"


class GoogleCalendarCallbackView(LoginRequiredMixin, View):
    """
    Обрабатывает callback от Google Calendar OAuth.
    Сохраняет credentials и обновляет статус подключения.
    """

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    REQUEST_TIMEOUT = 10

    def get(self, request):
        """Основной обработчик callback"""

        # Проверяем, что пользователь - переводчик
        if not isinstance(request.user, Interpreter):
            messages.error(request, "Not authorized")
            return redirect('interpreter_profile')

        # Валидация state
        if not self._validate_state(request):
            messages.error(request, "Invalid authentication request")
            return redirect('interpreter_profile')

        # Получение authorization code
        code = request.GET.get("code")
        if not code:
            error = request.GET.get("error")
            if error == "access_denied":
                messages.warning(request, "Calendar access was denied")
            else:
                messages.error(request, "Authorization failed")
            return redirect('interpreter_profile')

        try:
            # Обмениваем code на tokens
            tokens = self._exchange_code_for_tokens(code)

            # Сохраняем credentials
            self._save_credentials(request.user, tokens)

            # Обновляем статус в БД
            request.user.google_calendar_connected = True
            request.user.save(update_fields=['google_calendar_connected'])

            # Пробуем синхронизировать календарь
            self._initial_sync(request.user)

            messages.success(
                request,
                "Google Calendar connected successfully! "
                "Your availability will now sync automatically."
            )

            logger.info(f"Calendar connected for user {request.user.email}")

        except requests.RequestException as e:
            messages.error(request, "Failed to connect to Google. Please try again.")
            logger.error(f"Google Calendar OAuth connection error: {e}", exc_info=True)

        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            logger.error(f"Unexpected Calendar OAuth error: {e}", exc_info=True)

        finally:
            # Очищаем сессию
            request.session.pop('google_calendar_state', None)
            request.session.pop('google_calendar_user_id', None)

        return redirect('interpreter_profile')

    def _validate_state(self, request):
        """Проверяет state токен"""
        received_state = request.GET.get("state")
        saved_state = request.session.get('google_calendar_state')
        saved_user_id = request.session.get('google_calendar_user_id')

        return received_state and received_state == saved_state and saved_user_id == str(request.user.id)

    def _exchange_code_for_tokens(self, code):
        """
        Обменивает authorization code на access и refresh tokens

        Returns:
            dict: {'access_token': ..., 'refresh_token': ..., 'expires_in': ...}
        """
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        response = requests.post(
            self.TOKEN_URL,
            data=token_data,
            timeout=self.REQUEST_TIMEOUT
        )
        response.raise_for_status()

        tokens = response.json()

        # Проверяем наличие обязательных токенов
        if not tokens.get("access_token"):
            raise ValueError("No access token received")

        # Refresh token might not be present if access_type is not 'offline'
        # or if it's a subsequent authorization for the same user.
        # We should still save it if it exists.

        return tokens

    def _save_credentials(self, user, tokens):
        """Сохраняет credentials через GoogleCalendarService"""
        # Use GoogleCalendarCredentials model directly
        GoogleCalendarCredentials.objects.update_or_create(
            user=user,
            defaults={
                'token': tokens['access_token'],
                'refresh_token': tokens.get('refresh_token'),
                'token_uri': self.TOKEN_URL,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'scopes': ' '.join(settings.GOOGLE_OAUTH_SCOPES['calendar'])
            }
        )

    def _initial_sync(self, user):
        """Выполняет первоначальную синхронизацию календаря"""
        try:
            user.sync_availability_from_calendar()
            logger.info(f"Initial calendar sync completed for {user.email}")
        except Exception as e:
            logger.error(f"Initial sync failed for {user.email}: {e}")
            # Не прерываем процесс, просто логируем


class GoogleCalendarDisconnectView(LoginRequiredMixin, View):
    """
    Отключает Google Calendar от аккаунта переводчика.
    Удаляет сохранённые credentials и обновляет статус.
    """

    def post(self, request):
        """Обрабатывает отключение календаря"""

        if not isinstance(request.user, Interpreter):
            return JsonResponse({'error': 'Not authorized'}, status=403)

        try:
            # Delete credentials from our database
            GoogleCalendarCredentials.objects.filter(user=request.user).delete()

            # Update status in DB
            request.user.google_calendar_connected = False
            request.user.save(update_fields=['google_calendar_connected'])

            messages.success(request, "Google Calendar disconnected successfully")

            return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Error disconnecting calendar for {request.user.email}: {e}")
            return JsonResponse({
                'error': 'Failed to disconnect calendar'
            }, status=500)


class CalendarStatusAPIView(LoginRequiredMixin, View):
    """
    API endpoint для проверки статуса подключения календаря.
    Используется для обновления UI в реальном времени.
    """

    def get(self, request):
        """Возвращает статус подключения календаря"""

        if not isinstance(request.user, Interpreter):
            return JsonResponse({'connected': False})

        calendar_service = GoogleCalendarService(str(request.user.id))
        is_authorized = calendar_service.is_authorized()

        return JsonResponse({
            'connected': is_authorized,
            'user_id': str(request.user.id),
            'email': request.user.email,
        })
