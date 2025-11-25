from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.models import City, Client, LanguagePair, TranslationType


class InterpreterProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/interpreter/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cities'] = Client.objects.all()
        return ctx


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/dashboard.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/profile.html'


class OrdersView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/orders.html'


class NewOrderView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/new-order.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cities'] = City.objects.all()
        ctx['language_pairs'] = LanguagePair.objects.all()
        ctx['translation_types'] = TranslationType.objects.all()
        return ctx


class BillingView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/billing.html'


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/client/settings.html'
