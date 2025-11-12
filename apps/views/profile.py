from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.models import Client


class InterpreterProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/profile/interpreter-profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cities'] = Client.objects.all()
        return


class ClientProfileView(TemplateView):
    template_name = 'apps/profile/client-profile.html'
