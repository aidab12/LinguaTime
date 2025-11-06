# project/urls.py
from django.urls import path

from apps.views import RegisterInterpreterCreateView

urlpatterns = [
    path('signup/', RegisterInterpreterCreateView.as_view(), name='interpreter_signup'),
]