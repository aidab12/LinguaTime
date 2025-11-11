# project/urls.py
from django.urls import path

from apps.views import RegisterInterpreterCreateView, google_login, google_callback, RegisterCreateView, \
    ClientProfileView

urlpatterns = [
    path('signup/', RegisterInterpreterCreateView.as_view(), name='interpreter_signup'),
    path('signup/client/', RegisterCreateView.as_view(), name='client_signup'),

    path("auth/google-login", google_login, name='google_login'),
    path("auth/oauth2/callback", google_callback, name='google_callback'),

    path('client-profile/', ClientProfileView.as_view(), name='client_profile')
]
