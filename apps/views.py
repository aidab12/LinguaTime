import secrets
import urllib.parse
import requests

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView, TemplateView
from django_extensions.management.commands.export_emails import full_name

from apps.forms import CustomClientCreationForm, RegisterInterpreterModelForm
from apps.models import Interpreter, City, Language, Client
from root import settings


# class LoginAuthView(LoginView):
#     template_name = 'apps/auth/login.html'
#     next_page = reverse_lazy('')
#     form_class = CustomAuthenticationForm
#
#     def form_valid(self, form):
#         return super().form_valid(form)
#
#     def form_invalid(self, form):
#         return super().form_invalid(form)


# class LogoutPageView(View):
#     success_url = reverse_lazy('product_list_view')
#
#     def get(self, request, *args, **kwargs):
#         logout(request)
#         return redirect(self.success_url)


class RegisterCreateView(CreateView):
    """Регистрация обычных клиентов"""
    template_name = 'apps/auth/signup.html'
    form_class = CustomClientCreationForm
    success_url = reverse_lazy('client_profile')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cities'] = City.objects.all()
        ctx['languages'] = Language.objects.all()
        return ctx

    def form_valid(self, form):
        client = form.save()
        login(self.request, client)
        messages.success(self.request, "Client account created successfully!")
        return super().form_valid(form)


class RegisterInterpreterCreateView(CreateView):
    """Регистрация переводчиков"""
    model = Interpreter
    form_class = RegisterInterpreterModelForm
    template_name = 'apps/auth/signup.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cities'] = City.objects.all()
        ctx['languages'] = Language.objects.all()
        return ctx

    # success_url = reverse_lazy('interpreter_dashboard')

    def form_valid(self, form):
        interpreter = form.save()
        login(self.request, interpreter)  # автоматически авторизовать после регистрации
        messages.success(self.request, "Account successfully created.")

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class InterpreterProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/profile/interpreter-profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cities'] = Client.objects.all()
        return


# GOOGLE AUTH

def google_login(request):
    """Инициирует процесс авторизации через Google."""

    # Генерируем случайный state для защиты от CSRF
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state

    # Сохраняем тип пользователя из параметра запроса (если передан)
    user_type = request.GET.get('user_type', 'client')
    request.session['oauth_user_type'] = user_type

    scope = "email profile"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?response_type=code"
        f"&client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(settings.GOOGLE_REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(scope)}"
        f"&state={state}"
    )
    return redirect(auth_url)


class ClientProfileView(TemplateView):
    template_name = 'apps/profile/client-profile.html'


def google_callback(request):
    """
    Обрабатывает callback от Google после успешной авторизации.
    Создаёт или получает пользователя и авторизует его.
    """
    # 1. Проверяем state для защиты от CSRF
    received_state = request.GET.get("state")
    saved_state = request.session.get('oauth_state')

    if not received_state or received_state != saved_state:
        messages.error(request, "Invalid authentication request. Please try again.")
        return redirect('interpreter_signup')

    # 2. Получаем authorization code
    code = request.GET.get("code")
    if not code:
        messages.error(request, "Authorization failed. Please try again.")
        return redirect('interpreter_signup')

    try:
        # 3. Обмениваем code на access token
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        token_res = requests.post(
            "https://oauth2.googleapis.com/token",
            data=token_data,
            timeout=10  # Добавляем timeout
        )
        token_res.raise_for_status()
        token_json = token_res.json()
        access_token = token_json.get("access_token")

        if not access_token:
            raise ValueError("No access token received")

        # 4. Получаем информацию о пользователе
        user_info_res = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        user_info_res.raise_for_status()
        info = user_info_res.json()

        email = info.get("email")
        google_id = info.get("id")
        first_name = info.get("given_name", "")
        last_name = info.get("family_name", "")

        if not email or not google_id:
            raise ValueError("Email or Google ID not provided")

        user_type = request.session.get('oauth_user_type', 'client')

        # 6. Создаём или получаем пользователя
        if user_type == 'interpreter':
            user, created = Interpreter.objects.get_or_create(
                email=email,  # Используем email как уникальный идентификатор
                defaults={

                    "first_name": first_name,
                    "last_name": last_name,
                }
            )
            success_url = 'interpreter_profile'
        else:
            # Предполагаем, что у вас есть модель Client
            user, created = Client.objects.get_or_create(
                email=email,
                defaults={

                    "first_name": first_name,
                    "last_name": last_name,
                }
            )
            success_url = 'client_profile'

        # 7. Устанавливаем непригодный пароль (пользователь использует Google)
        if created:
            user.set_unusable_password()
            user.save()
            messages.success(request, "Account created successfully!")
        else:
            messages.success(request, "Welcome back!")

        # 8. Авторизуем пользователя
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # 9. Очищаем сессию
        request.session.pop('oauth_state', None)
        request.session.pop('oauth_user_type', None)

        return redirect(success_url)

    except requests.RequestException as e:
        messages.error(request, "Failed to connect to Google. Please try again.")
        return redirect('interpreter_signup')
    except ValueError as e:
        messages.error(request, f"Authentication error: {str(e)}")
        return redirect('interpreter_signup')
    except Exception as e:
        # Логируем ошибку для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Google OAuth error: {str(e)}", exc_info=True)

        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('interpreter_signup')
