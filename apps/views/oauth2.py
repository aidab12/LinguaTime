import logging
import secrets
import urllib.parse

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.views import View

from apps.models import Client, Interpreter

logger = logging.getLogger(__name__)


class GoogleLoginView(View):
    """
    Инициирует процесс авторизации через Google OAuth 2.0.

    GET параметры:
        user_type (str, optional): 'interpreter' или 'client'. По умолчанию 'client'
    """

    OAUTH_SCOPE = (
        "https://www.googleapis.com/auth/userinfo.email "
        "https://www.googleapis.com/auth/userinfo.profile "
        # "https://www.googleapis.com/auth/calendar"
    )

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"

    def get(self, request):
        """Генерирует URL для авторизации и редиректит пользователя."""

        # Генерируем CSRF-токен для защиты
        state = self._generate_state()
        request.session['oauth_state'] = state

        # Сохраняем тип пользователя
        user_type = self._get_user_type(request)
        request.session['oauth_user_type'] = user_type

        # Строим URL для авторизации
        auth_url = self._build_auth_url(state)

        return redirect(auth_url)

    def _generate_state(self):
        """Генерирует случайный state-токен для защиты от CSRF."""
        return secrets.token_urlsafe(32)

    def _get_user_type(self, request):
        """Извлекает и валидирует тип пользователя из запроса."""
        user_type = request.GET.get('user_type', 'client')
        # Валидация: только допустимые типы
        return user_type if user_type in ['client', 'interpreter'] else 'client'

    def _build_auth_url(self, state):
        """Создаёт URL для редиректа на Google OAuth."""
        params = {
            'response_type': 'code',
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'scope': self.OAUTH_SCOPE,
            'state': state,
        }

        query_string = urllib.parse.urlencode(params)
        return f"{self.GOOGLE_AUTH_URL}?{query_string}"


class GoogleCallbackView(View):
    """
    Обрабатывает callback от Google после успешной авторизации.
    Создаёт/получает пользователя и выполняет вход в систему.
    """

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

    # Таймаут для HTTP-запросов
    REQUEST_TIMEOUT = 10

    # Маппинг типов пользователей на модели и URL
    USER_TYPE_CONFIG = {
        'interpreter': {
            'model': Interpreter,
            'success_url': 'interpreter_profile',
            'error_url': 'interpreter_signup',
        },
        'client': {
            'model': Client,
            'success_url': 'client_dashboard',
            'error_url': 'login_page',
        }
    }

    def get(self, request):
        """Основной обработчик callback от Google."""

        # 1. Валидация state (защита от CSRF)
        if not self._validate_state(request):
            messages.error(request, "Invalid authentication request. Please try again.")
            return redirect('interpreter_signup')

        # 2. Получение authorization code
        code = request.GET.get("code")
        if not code:
            messages.error(request, "Authorization failed. Please try again.")
            return redirect('interpreter_signup')

        try:
            # 3. Обмен code на access token
            access_token = self._exchange_code_for_token(code)

            # 4. Получение информации о пользователе
            user_info = self._fetch_user_info(access_token)

            # 5. Создание/получение пользователя
            user, created = self._get_or_create_user(request, user_info)

            # 6. Авторизация пользователя
            self._login_user(request, user, created)

            # 7. Очистка сессии и редирект
            return self._cleanup_and_redirect(request, user)

        except requests.RequestException:
            messages.error(request, "Failed to connect to Google. Please try again.")
            logger.error("Google OAuth connection error", exc_info=True)
            return redirect('interpreter_signup')

        except ValueError as e:
            messages.error(request, f"Authentication error: {str(e)}")
            logger.error(f"Google OAuth validation error: {str(e)}", exc_info=True)
            return redirect('interpreter_signup')

        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            logger.error(f"Unexpected Google OAuth error: {str(e)}", exc_info=True)
            return redirect('interpreter_signup')

    def _validate_state(self, request):
        """Проверяет state-токен для защиты от CSRF-атак."""
        received_state = request.GET.get("state")
        saved_state = request.session.get('oauth_state')
        return received_state and received_state == saved_state

    def _exchange_code_for_token(self, code):
        """
        Обменивает authorization code на access token.

        Args:
            code (str): Authorization code от Google

        Returns:
            str: Access token

        Raises:
            requests.RequestException: При ошибке HTTP-запроса
            ValueError: Если токен не получен
        """
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        response = requests.post(
            self.TOKEN_URL,
            data=token_data,
            timeout=self.REQUEST_TIMEOUT
        )
        response.raise_for_status()

        token_json = response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            raise ValueError("No access token received from Google")

        return access_token

    def _fetch_user_info(self, access_token):
        """
        Получает информацию о пользователе от Google.

        Args:
            access_token (str): Access token для API

        Returns:
            dict: Информация о пользователе

        Raises:
            requests.RequestException: При ошибке HTTP-запроса
            ValueError: Если обязательные поля отсутствуют
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(
            self.USERINFO_URL,
            headers=headers,
            timeout=self.REQUEST_TIMEOUT
        )
        response.raise_for_status()

        user_info = response.json()

        # Валидация обязательных полей
        if not user_info.get("email") or not user_info.get("id"):
            raise ValueError("Email or Google ID not provided by Google")

        return user_info

    def _get_or_create_user(self, request, user_info):
        """
        Создаёт нового пользователя или получает существующего.

        Args:
            request: HTTP request объект
            user_info (dict): Информация о пользователе от Google

        Returns:
            tuple: (user_instance, created_flag)
        """
        email = user_info.get("email")
        first_name = user_info.get("given_name", "")
        last_name = user_info.get("family_name", "")

        # Определяем тип пользователя и соответствующую модель
        user_type = request.session.get('oauth_user_type', 'client')
        config = self.USER_TYPE_CONFIG.get(user_type, self.USER_TYPE_CONFIG['client'])

        UserModel = config['model']

        # Создаём или получаем пользователя
        user, created = UserModel.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
            }
        )

        # Для новых пользователей устанавливаем непригодный пароль
        if created:
            user.set_unusable_password()
            user.save()

        return user, created

    def _login_user(self, request, user, created):
        """
        Авторизует пользователя в системе и показывает соответствующее сообщение.

        Args:
            request: HTTP request объект
            user: Экземпляр пользователя
            created (bool): Флаг создания нового пользователя
        """
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        if created:
            messages.success(request, "Account created successfully!")
        else:
            messages.success(request, "Welcome back!")

    def _cleanup_and_redirect(self, request, user):
        """
        Очищает сессию и перенаправляет на соответствующую страницу.

        Args:
            request: HTTP request объект
            user: Экземпляр пользователя

        Returns:
            HttpResponseRedirect
        """
        # Очищаем OAuth данные из сессии
        request.session.pop('oauth_state', None)
        user_type = request.session.pop('oauth_user_type', 'client')

        # Определяем URL для редиректа
        config = self.USER_TYPE_CONFIG.get(user_type, self.USER_TYPE_CONFIG['client'])
        success_url = config['success_url']

        return redirect(success_url)
