from django.urls import path

from apps.views.auth import RegisterInterpreterCreateView, RegisterCreateView, LoginView
from apps.views.oauth2 import google_login, google_callback
from apps.views.profile import DashboardView, ProfileView, OrdersView, NewOrderView, BillingView, SettingsView
from apps.views.views import TestAuthView

app_name = 'apps'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', RegisterInterpreterCreateView.as_view(), name='interpreter_signup'),
    path('signup/client/', RegisterCreateView.as_view(), name='client_signup'),

    path("auth/google-login", google_login, name='google_login'),
    path("auth/oauth2/callback", google_callback, name='google_callback'),

    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('orders/', OrdersView.as_view(), name='orders'),
    path('new-order/', NewOrderView.as_view(), name='new-order'),
    path('billing/', BillingView.as_view(), name='billing'),
    path('settings/', SettingsView.as_view(), name='settings'),

    path('test-auth/', TestAuthView.as_view())
]
