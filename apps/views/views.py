from django.views.generic import TemplateView


class TestAuthView(TemplateView):
    template_name = 'apps/auth/testsignup.html'

