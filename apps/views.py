from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView

from apps.forms import CustomClientCreationForm


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


class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/main_filter.html'

