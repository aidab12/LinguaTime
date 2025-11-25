from django.urls import path

from apps.views import (BillingView, DashboardView, LoginFormView, LogoutView,
                        NewOrderView, OrdersView, ProfileView,
                        RegisterCreateView, RegisterInterpreterCreateView,
                        SettingsView, TelegramWebhookView, RoleSwitchView, GoogleCallbackView,
                        GoogleLoginView, InterpreterProfileView, GoogleCalendarWebhookView, OrderCreateView,
                        OrderSendOffersView, CalendarStatusAPIView,
                        GoogleCalendarAuthorizeView,
                        GoogleCalendarCallbackView,
                        GoogleCalendarDisconnectView)

urlpatterns = [
    path('', LoginFormView.as_view(), name='login_page'),
    path('signup/', RegisterInterpreterCreateView.as_view(), name='interpreter_signup'),
    path('signup/client/', RegisterCreateView.as_view(), name='client_signup'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path("auth/google-login/", GoogleLoginView.as_view(), name='google_login'),
    path("auth/oauth2/callback/", GoogleCallbackView.as_view(), name='google_callback'),

    path('client/dashboard/', DashboardView.as_view(), name='client_dashboard'),
    path('client/profile/', ProfileView.as_view(), name='client_profile'),
    path('cliend/orders/', OrdersView.as_view(), name='client_orders'),
    path('client/new-order/', NewOrderView.as_view(), name='client_new_order'),
    path('client/billing/', BillingView.as_view(), name='client_billing'),
    path('client/settings/', SettingsView.as_view(), name='client_settings'),

    path('interpreter/profile/', InterpreterProfileView.as_view(), name='interpreter_profile'),

    # Role Switching
    path('switch-role/', RoleSwitchView.as_view(), name='switch_role'),

    # Google Calendar Integration URLs
    path('calendar/authorize/', GoogleCalendarAuthorizeView.as_view(), name='google_calendar_authorize'),
    path('calendar/oauth2/callback/', GoogleCalendarCallbackView.as_view(), name='google_calendar_callback'),
    path('calendar/disconnect/', GoogleCalendarDisconnectView.as_view(), name='google_calendar_disconnect'),
    path('calendar/status/', CalendarStatusAPIView.as_view(), name='google_calendar_status'),

    # Webhook Endpoints
    path('webhook/google-calendar/', GoogleCalendarWebhookView.as_view(), name='google_calendar_webhook'),
    path('webhook/telegram/', TelegramWebhookView.as_view(), name='telegram_webhook'),

    # Order Workflow API
    path('api/orders/create/', OrderCreateView.as_view(), name='order_create'),
    path('api/orders/<uuid:order_id>/send-offers/', OrderSendOffersView.as_view(), name='order_send_offers'),
]
