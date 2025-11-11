from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.options import ModelAdmin
from django.template.loader import get_template

from apps.models import Interpreter, Client, Order, Booking, User
from apps.models.cities import Country, Region, City
from apps.models.reviews import Review


@admin.register(Interpreter)
class InterpreterModelAdmin(ModelAdmin):
    pass


@admin.register(Client)
class ClientModelAdmin(ModelAdmin):
    fields = 'email',


@admin.register(Order)
class OrderModelAdmin(ModelAdmin):
    pass


@admin.register(Booking)
class BookingModelAdmin(ModelAdmin):
    pass


@admin.register(Review)
class ReviewModelAdmin(ModelAdmin):
    pass


@admin.register(User)
class UserModelAdmin(ModelAdmin):
    pass


class RegionInline(admin.TabularInline):
    model = Region


@admin.register(Country)
class CountryModelAdmin(ModelAdmin):
    inlines = RegionInline,
    fields = 'name',


@admin.register(City)
class CityModelAdmin(ModelAdmin):
    pass