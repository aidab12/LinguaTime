from django.urls import path

from apps.views import RegisterInterpreterCreateView, RegisterCreateView, LoginView, \
    DashboardView, ProfileView, OrdersView, NewOrderView, BillingView, SettingsView
from apps.views.oauth2 import GoogleLoginView, GoogleCallbackView
from apps.views.profile import InterpreterProfileView

urlpatterns = [
    path('', LoginView.as_view(), name='login_page'),
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

]
