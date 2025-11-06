# project/urls.py
from django.contrib import admin
from django.urls import path

from apps.views import RegisterCreateView

urlpatterns = [
    # path('', include('social_django.urls', namespace='social')),
    path('register/', RegisterCreateView.as_view(), name='register'),
    # path('login/', views.custom_login, name='login'),
    # path('', views.home, name='home'),
]