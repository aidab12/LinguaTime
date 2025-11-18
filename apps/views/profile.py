from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.models import City, Client, LanguagePair, TranslationType


class InterpreterProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/interpreter/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        ctx['cities'] = Client.objects.all()
        return ctx


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['client'] = self.request.user
        return ctx


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['client'] = self.request.user
        return ctx


class OrdersView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/orders.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['client'] = self.request.user
        return ctx


class NewOrderView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/new-order.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['client'] = self.request.user
        ctx['cities'] = City.objects.all()
        ctx['language_pairs'] = LanguagePair.objects.all()
        ctx['translation_types'] = TranslationType.objects.all()
        return ctx


class BillingView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/billing.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['client'] = self.request.user
        return ctx


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/settings.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['client'] = self.request.user
        return ctx
