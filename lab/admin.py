from django.contrib import admin
from .models import Location, Appliance

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_type', 'user', 'created_at')
    list_filter = ('location_type', 'user')

@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    # Yangi maydonlarga moslashtirildi
    list_display = ('appliance_name', 'location', 'user', 'power_watts', 'hours_per_day', 'monthly_kwh')
    list_filter = ('location', 'user')