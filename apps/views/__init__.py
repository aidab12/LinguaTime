from apps.views.auth import (LoginFormView, LogoutView, RegisterCreateView,
                             RegisterInterpreterCreateView)
from apps.views.oauth2 import GoogleCallbackView, GoogleLoginView
from apps.views.profile import (BillingView, DashboardView, NewOrderView,
                                OrdersView, ProfileView, SettingsView)

__all__ = ['LoginFormView', 'LogoutView', 'RegisterCreateView', 'RegisterInterpreterCreateView',
           'DashboardView', 'ProfileView', 'OrdersView', 'NewOrderView', 'BillingView', 'SettingsView']
