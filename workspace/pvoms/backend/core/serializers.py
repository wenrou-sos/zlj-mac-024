from rest_framework import serializers

from .models import (Alarm, CleaningPlan, DefectRecord, Device, InspectionOrder,
                     PowerData, Station)


class StationSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    today_energy = serializers.FloatField(read_only=True, default=0)
    active_alarms = serializers.IntegerField(read_only=True, default=0)
    device_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Station
        fields = "__all__"


class DeviceSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_device_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    station_name = serializers.CharField(source="station.name", read_only=True)

    class Meta:
        model = Device
        fields = "__all__"


class PowerDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerData
        fields = ["date", "energy_kwh", "peak_power_kw", "equivalent_hours", "pr", "irradiance"]


class AlarmSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    station_name = serializers.CharField(source="station.name", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True, default=None)

    class Meta:
        model = Alarm
        fields = "__all__"
        read_only_fields = ["created_at", "handled_at"]


class InspectionOrderSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_order_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    station_name = serializers.CharField(source="station.name", read_only=True)

    class Meta:
        model = InspectionOrder
        fields = "__all__"
        read_only_fields = ["created_at", "finished_at"]


class CleaningPlanSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    station_name = serializers.CharField(source="station.name", read_only=True)

    class Meta:
        model = CleaningPlan
        fields = "__all__"
        read_only_fields = ["created_at", "finished_at"]


class DefectRecordSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    station_name = serializers.CharField(source="station.name", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True, default=None)

    class Meta:
        model = DefectRecord
        fields = "__all__"
        read_only_fields = ["created_at", "resolved_at"]
