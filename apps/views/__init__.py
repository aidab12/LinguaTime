from apps.views.auth import (LoginFormView, LogoutView, RegisterCreateView,
                             RegisterInterpreterCreateView)
from apps.views.google_calendar_oauth import (CalendarStatusAPIView,
                                              GoogleCalendarAuthorizeView,
                                              GoogleCalendarCallbackView,
                                              GoogleCalendarDisconnectView)
from apps.views.google_calendar_webhook import GoogleCalendarWebhookView
from apps.views.oauth2 import GoogleCallbackView, GoogleLoginView
from apps.views.order_workflow import OrderCreateView, OrderSendOffersView
from apps.views.profile import (BillingView, DashboardView, NewOrderView,
                                OrdersView, ProfileView, SettingsView, InterpreterProfileView)
from apps.views.role_switch import RoleSwitchView
from apps.views.telegram_webhook import TelegramWebhookView
