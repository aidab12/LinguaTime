from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseRedirect


class LoginNotRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            return HttpResponseRedirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
