from django.contrib import admin

from .models import (Alarm, CleaningPlan, DefectRecord, Device, InspectionOrder,
                     PowerData, Station)


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "city", "capacity_kwp", "status", "grid_date")
    list_filter = ("status",)
    search_fields = ("name", "code")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "station", "device_type", "status")
    list_filter = ("device_type", "status", "station")


@admin.register(PowerData)
class PowerDataAdmin(admin.ModelAdmin):
    list_display = ("station", "date", "energy_kwh", "equivalent_hours", "pr")
    list_filter = ("station",)


@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ("title", "station", "level", "status", "created_at")
    list_filter = ("level", "status")


@admin.register(InspectionOrder)
class InspectionOrderAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "station", "assignee", "status", "plan_date")
    list_filter = ("status", "order_type")


@admin.register(CleaningPlan)
class CleaningPlanAdmin(admin.ModelAdmin):
    list_display = ("code", "station", "area", "plan_date", "executor", "status")
    list_filter = ("status",)


@admin.register(DefectRecord)
class DefectRecordAdmin(admin.ModelAdmin):
    list_display = ("code", "station", "level", "status", "reporter", "found_at")
    list_filter = ("level", "status")
