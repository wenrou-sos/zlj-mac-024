import math
import random
from datetime import date, timedelta

from django.db.models import Count, FloatField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import (Alarm, CleaningPlan, DefectRecord, Device, InspectionOrder,
                     PowerData, Station)
from .serializers import (AlarmSerializer, CleaningPlanSerializer,
                          DefectRecordSerializer, DeviceSerializer,
                          InspectionOrderSerializer, PowerDataSerializer,
                          StationSerializer)


def _filtered(qs, request, mapping):
    """按 query params 做等值过滤，mapping: {param: orm_field}"""
    for param, field in mapping.items():
        value = request.query_params.get(param)
        if value:
            qs = qs.filter(**{field: value})
    return qs


def _today_energy_subquery():
    """当日发电量子查询（避免与 Count 注解混用导致 JOIN 交叉相乘）"""
    return Coalesce(
        Subquery(
            PowerData.objects.filter(station=OuterRef("pk"), date=date.today())
            .values("station").annotate(s=Sum("energy_kwh")).values("s"),
            output_field=FloatField(),
        ), 0.0)


class StationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StationSerializer

    def get_queryset(self):
        qs = Station.objects.annotate(
            today_energy=_today_energy_subquery(),
            active_alarms=Count("alarms", filter=Q(alarms__status__in=["open", "processing"]),
                                distinct=True),
            device_count=Count("devices", distinct=True),
        )
        return _filtered(qs, self.request, {"status": "status"})

    @action(detail=True, methods=["get"])
    def power(self, request, pk=None):
        """日发电序列 ?days=30"""
        station = self.get_object()
        days = min(int(request.query_params.get("days", 30)), 365)
        since = date.today() - timedelta(days=days - 1)
        qs = PowerData.objects.filter(station=station, date__gte=since).order_by("date")
        return Response(PowerDataSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def power_hourly(self, request, pk=None):
        """今日逐时功率曲线（由当日发电量合成的演示数据）"""
        station = self.get_object()
        today = date.today()
        rec = PowerData.objects.filter(station=station, date=today).first()
        total = rec.energy_kwh if rec else station.capacity_kwp * 4.0
        rng = random.Random(f"{station.id}-{today}")
        raw = []
        for h in range(24):
            # 日照曲线：6 点日出、19 点日落，正午最强，叠加云扰动
            x = (h - 6) / 13 * math.pi
            base = max(0.0, math.sin(x)) ** 1.25 if 0 < x < math.pi else 0.0
            raw.append(base * (0.75 + 0.5 * rng.random()) if base > 0 else 0.0)
        s = sum(raw) or 1.0
        data = [{"hour": f"{h:02d}:00", "power_kw": round(total * raw[h] / s, 1)}
                for h in range(24)]
        return Response(data)

    @action(detail=True, methods=["get"])
    def devices(self, request, pk=None):
        return Response(DeviceSerializer(self.get_object().devices.all(), many=True).data)


class DeviceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeviceSerializer

    def get_queryset(self):
        qs = Device.objects.select_related("station")
        return _filtered(qs, self.request, {"station": "station_id", "status": "status",
                                            "type": "device_type"})


class AlarmViewSet(viewsets.ModelViewSet):
    serializer_class = AlarmSerializer

    def get_queryset(self):
        qs = Alarm.objects.select_related("station", "device")
        return _filtered(qs, self.request, {"station": "station_id", "status": "status",
                                            "level": "level"})

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """开始处理：未处理 -> 处理中"""
        alarm = self.get_object()
        alarm.status = "processing"
        alarm.handler = request.data.get("handler", alarm.handler)
        alarm.save(update_fields=["status", "handler"])
        return Response(AlarmSerializer(alarm).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """处理完成 -> 已处理"""
        alarm = self.get_object()
        alarm.status = "resolved"
        alarm.handler = request.data.get("handler", alarm.handler)
        alarm.handled_at = timezone.now()
        alarm.save(update_fields=["status", "handler", "handled_at"])
        return Response(AlarmSerializer(alarm).data)


class InspectionOrderViewSet(viewsets.ModelViewSet):
    serializer_class = InspectionOrderSerializer

    def get_queryset(self):
        qs = InspectionOrder.objects.select_related("station")
        return _filtered(qs, self.request, {"station": "station_id", "status": "status",
                                            "type": "order_type"})

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        order = self.get_object()
        order.status = "in_progress"
        order.save(update_fields=["status"])
        return Response(InspectionOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        order = self.get_object()
        order.status = "done"
        order.result = request.data.get("result", order.result)
        order.finished_at = timezone.now()
        order.save(update_fields=["status", "result", "finished_at"])
        return Response(InspectionOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.status = "cancelled"
        order.save(update_fields=["status"])
        return Response(InspectionOrderSerializer(order).data)


class CleaningPlanViewSet(viewsets.ModelViewSet):
    serializer_class = CleaningPlanSerializer

    def get_queryset(self):
        qs = CleaningPlan.objects.select_related("station")
        return _filtered(qs, self.request, {"station": "station_id", "status": "status"})

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        plan = self.get_object()
        plan.status = "in_progress"
        plan.save(update_fields=["status"])
        return Response(CleaningPlanSerializer(plan).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        plan = self.get_object()
        plan.status = "done"
        plan.note = request.data.get("note", plan.note)
        plan.finished_at = timezone.now()
        plan.save(update_fields=["status", "note", "finished_at"])
        return Response(CleaningPlanSerializer(plan).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        plan = self.get_object()
        plan.status = "cancelled"
        plan.save(update_fields=["status"])
        return Response(CleaningPlanSerializer(plan).data)


class DefectRecordViewSet(viewsets.ModelViewSet):
    serializer_class = DefectRecordSerializer

    def get_queryset(self):
        qs = DefectRecord.objects.select_related("station", "device")
        return _filtered(qs, self.request, {"station": "station_id", "status": "status",
                                            "level": "level"})

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        defect = self.get_object()
        defect.status = "processing"
        defect.handler = request.data.get("handler", defect.handler)
        defect.save(update_fields=["status", "handler"])
        return Response(DefectRecordSerializer(defect).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        defect = self.get_object()
        defect.status = "resolved"
        defect.handler = request.data.get("handler", defect.handler)
        defect.solution = request.data.get("solution", defect.solution)
        defect.resolved_at = timezone.now()
        defect.save(update_fields=["status", "handler", "solution", "resolved_at"])
        return Response(DefectRecordSerializer(defect).data)


@api_view(["GET"])
def overview(request):
    """驾驶舱总览数据"""
    today = date.today()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    energy = lambda qs: round(qs or 0, 1)
    power = PowerData.objects

    device_status = {row["status"]: row["n"] for row in
                     Device.objects.values("status").annotate(n=Count("id"))}
    alarm_level = {row["level"]: row["n"] for row in
                   Alarm.objects.exclude(status="resolved")
                   .values("level").annotate(n=Count("id"))}

    # 近 30 天全场站发电趋势
    since = today - timedelta(days=29)
    trend_qs = (power.filter(date__gte=since).values("date")
                .annotate(energy=Sum("energy_kwh")).order_by("date"))
    trend = [{"date": r["date"].strftime("%m-%d"), "energy": round(r["energy"], 1)}
             for r in trend_qs]

    # 各电站今日发电 + 状态
    stations = []
    for s in Station.objects.annotate(
            today_energy=_today_energy_subquery(),
            active_alarms=Count("alarms",
                                filter=Q(alarms__status__in=["open", "processing"]),
                                distinct=True)):
        stations.append({
            "id": s.id, "name": s.name, "code": s.code, "city": s.city,
            "capacity_kwp": s.capacity_kwp, "status": s.status,
            "today_energy": round(s.today_energy, 1), "active_alarms": s.active_alarms,
        })

    return Response({
        "station_count": Station.objects.count(),
        "total_capacity_kwp": round(Station.objects.aggregate(
            v=Coalesce(Sum("capacity_kwp"), 0.0))["v"], 1),
        "today_energy": energy(power.filter(date=today).aggregate(v=Sum("energy_kwh"))["v"]),
        "month_energy": energy(power.filter(date__gte=month_start).aggregate(v=Sum("energy_kwh"))["v"]),
        "year_energy": energy(power.filter(date__gte=year_start).aggregate(v=Sum("energy_kwh"))["v"]),
        "device_total": Device.objects.count(),
        "device_status": device_status,
        "active_alarms": Alarm.objects.exclude(status="resolved").count(),
        "alarm_level": alarm_level,
        "pending_inspections": InspectionOrder.objects.filter(
            status__in=["pending", "in_progress"]).count(),
        "pending_cleanings": CleaningPlan.objects.filter(
            status__in=["planned", "in_progress"]).count(),
        "open_defects": DefectRecord.objects.exclude(status="resolved").count(),
        "trend": trend,
        "stations": stations,
        "recent_alarms": AlarmSerializer(
            Alarm.objects.select_related("station", "device")
            .exclude(status="resolved").order_by("-created_at")[:8], many=True).data,
    })
