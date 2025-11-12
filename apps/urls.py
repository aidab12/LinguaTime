from django.urls import path

from apps.views.auth import RegisterInterpreterCreateView, RegisterCreateView
from apps.views.oauth2 import google_login, google_callback
from apps.views.profile import ClientProfileView
from apps.views.views import TestAuthView

urlpatterns = [
    path('signup/', RegisterInterpreterCreateView.as_view(), name='interpreter_signup'),
    path('signup/client/', RegisterCreateView.as_view(), name='client_signup'),

    path("auth/google-login", google_login, name='google_login'),
    path("auth/oauth2/callback", google_callback, name='google_callback'),

    path('client-profile/', ClientProfileView.as_view(), name='client_profile'),

    path('test-auth/', TestAuthView.as_view())
]
