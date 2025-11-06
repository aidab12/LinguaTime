from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView, TemplateView

from apps.forms import CustomClientCreationForm, RegisterInterpreterModelForm
from apps.models import Interpreter, City, Language


# class LoginAuthView(LoginView):
#     template_name = 'apps/auth/login.html'
#     next_page = reverse_lazy('')
#     form_class = CustomAuthenticationForm
#
#     def form_valid(self, form):
#         return super().form_valid(form)
#
#     def form_invalid(self, form):
#         return super().form_invalid(form)


# class LogoutPageView(View):
#     success_url = reverse_lazy('product_list_view')
#
#     def get(self, request, *args, **kwargs):
#         logout(request)
#         return redirect(self.success_url)


class RegisterCreateView(CreateView):
    template_name = 'apps/auth/singup.html'
    form_class = CustomClientCreationForm


class RegisterInterpreterCreateView(CreateView):
    model = Interpreter
    form_class = RegisterInterpreterModelForm
    template_name = 'apps/auth/singup.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cities'] = City.objects.all()
        ctx['languages'] = Language.objects.all()
        return ctx

    # success_url = reverse_lazy('interpreter_dashboard')



    def form_valid(self, form):
        interpreter = form.save()
        login(self.request, interpreter) # автоматически авторизовать после регистрации
        messages.success(self.request, "Account successfully created.")

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)




class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/main_filter.html'
