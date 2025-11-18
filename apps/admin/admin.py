from django.contrib import admin
from django.contrib.admin.options import ModelAdmin

from apps.models import Interpreter, Client, Order, Booking, User, Review, Country, Region, City, Language, \
    Availability, OrderInterpreter
from apps.models.languages import TranslationType, LanguagePair


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


@admin.register(Language)
class LanguageModelAdmin(ModelAdmin):
    pass


@admin.register(Availability)
class AvailabilityModelAdmin(ModelAdmin):
    pass


@admin.register(OrderInterpreter)
class OrderInterpreterModelAdmin(ModelAdmin):
    pass


@admin.register(TranslationType)
class TranslationTypeModelAdmin(ModelAdmin):
    pass


@admin.register(LanguagePair)
class LanguagePairModelAdmin(ModelAdmin):
    pass
