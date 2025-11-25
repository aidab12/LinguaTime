from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View


class RoleSwitchView(LoginRequiredMixin, View):
    """
    View для переключения между ролями переводчика и клиента.
    Доступно только для пользователей с user_type = BOTH.
    """

    def post(self, request):
        """Обрабатывает переключение роли"""
        new_role = request.POST.get('role')

        # Проверяем, что пользователь может иметь несколько ролей
        if request.user.user_type != request.user.UserType.BOTH:
            messages.error(request, "У вас нет доступа к переключению ролей")
            return redirect('/')

        # Валидация новой роли
        if new_role not in [request.user.UserType.INTERPRETER, request.user.UserType.CLIENT]:
            messages.error(request, "Неверная роль")
            return redirect('/')

        # Переключаем роль
        if request.user.switch_role(new_role):
            if new_role == request.user.UserType.INTERPRETER:
                messages.success(request, "Вы переключились на роль переводчика")
                return redirect('interpreter_dashboard')
            else:
                messages.success(request, "Вы переключились на роль клиента")
                return redirect('client_dashboard')
        else:
            messages.error(request, "Не удалось переключить роль")
            return redirect('/')
