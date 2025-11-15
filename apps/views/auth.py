from django.contrib import messages
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView

from apps.forms import RegisterClientModelForm, RegisterInterpreterModelForm, LoginForm
from apps.models import Interpreter, City, Language
from apps.views.mixins import LoginNotRequiredMixin


class LoginView(LoginNotRequiredMixin, FormView):
    template_name = 'apps/auth/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('dashboard')
    redirect_authenticated_user = True

    def form_valid(self, form):
        login(self.request, form.user)
        user_type = form.cleaned_data['user_type']

        if user_type == 'interpreter':
            return redirect('interpreter_profile')
        return redirect('apps:dashboard')


class RegisterCreateView(CreateView):
    """Регистрация обычных клиентов"""
    template_name = 'apps/auth/signup.html'
    form_class = RegisterClientModelForm
    success_url = reverse_lazy('dashboard')

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

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class RegisterInterpreterCreateView(CreateView):
    """Регистрация переводчиков"""
    model = Interpreter
    form_class = RegisterInterpreterModelForm
    template_name = 'apps/auth/signup.html'
    success_url = reverse_lazy('interpreter_signup')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cities'] = City.objects.all()
        ctx['languages'] = Language.objects.all()
        return ctx

    def form_valid(self, form):
        interpreter = form.save()
        login(self.request, interpreter)  # автоматически авторизовать после регистрации
        messages.success(self.request, "Account successfully created.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)
