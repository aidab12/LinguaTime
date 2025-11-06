from django.contrib import admin

from apps.models import Interpreter, Client, Order, Booking, User
from apps.models.reviews import Review


@admin.register(Interpreter)
class InterpreterModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Client)
class ClientModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Booking)
class BookingModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Review)
class ReviewModelAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    pass
