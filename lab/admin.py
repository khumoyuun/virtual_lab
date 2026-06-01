from django.contrib import admin
from .models import Appliance, ConsumptionRecord

@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'avg_power_watts')

@admin.register(ConsumptionRecord)
class ConsumptionRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'appliance_name', 'power_watts', 'hours_per_day', 'monthly_kwh', 'co2_footprint')
    readonly_fields = ('daily_kwh', 'monthly_kwh', 'co2_footprint', 'auto_tip') # Bu maydonlar avtomatik to'ldiriladi