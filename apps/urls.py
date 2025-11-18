from django.urls import path

from apps.views import (BillingView, DashboardView, LoginFormView, NewOrderView,
                        OrdersView, ProfileView, RegisterCreateView,
                        RegisterInterpreterCreateView, SettingsView)
from apps.views.google_calendar_oauth import (CalendarStatusAPIView,
                                              GoogleCalendarAuthorizeView,
                                              GoogleCalendarCallbackView,
                                              GoogleCalendarDisconnectView)
from apps.views.oauth2 import GoogleCallbackView, GoogleLoginView
from apps.views.profile import InterpreterProfileView

urlpatterns = [
    path('', LoginFormView.as_view(), name='login_page'),
    path('signup/', RegisterInterpreterCreateView.as_view(), name='interpreter_signup'),
    path('signup/client/', RegisterCreateView.as_view(), name='client_signup'),

    path("auth/google-login/", GoogleLoginView.as_view(), name='google_login'),
    path("auth/oauth2/callback/", GoogleCallbackView.as_view(), name='google_callback'),

    path('client/dashboard/', DashboardView.as_view(), name='client_dashboard'),
    path('client/profile/', ProfileView.as_view(), name='client_profile'),
    path('cliend/orders/', OrdersView.as_view(), name='client_orders'),
    path('client/new-order/', NewOrderView.as_view(), name='client_new_order'),
    path('client/billing/', BillingView.as_view(), name='client_billing'),
    path('client/settings/', SettingsView.as_view(), name='client_settings'),

    path('interpreter/profile/', InterpreterProfileView.as_view(), name='interpreter_profile'),

    # Google Calendar Integration URLs
    path('calendar/authorize/', GoogleCalendarAuthorizeView.as_view(), name='google_calendar_authorize'),
    path('calendar/oauth2/callback/', GoogleCalendarCallbackView.as_view(), name='google_calendar_callback'),
    path('calendar/disconnect/', GoogleCalendarDisconnectView.as_view(), name='google_calendar_disconnect'),
    path('calendar/status/', CalendarStatusAPIView.as_view(), name='google_calendar_status'),
]
