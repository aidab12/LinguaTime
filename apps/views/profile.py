from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.models import Client


class InterpreterProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/profile/interpreter-profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cities'] = Client.objects.all()
        return


class DashboardView(TemplateView):
    template_name = 'apps/profile/dashboard.html'


class ProfileView(TemplateView):
    template_name = 'apps/profile/profile.html'


class OrdersView(TemplateView):
    template_name = 'apps/profile/orders.html'


class NewOrderView(TemplateView):
    template_name = 'apps/profile/new-order.html'


class BillingView(TemplateView):
    template_name = 'apps/profile/billing.html'


class SettingsView(TemplateView):
    template_name = 'apps/profile/settings.html'
