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


def _gen_code(prefix):
    """生成全局唯一业务编号：前缀+日期+随机序号"""
    today = date.today()
    for _ in range(10):
        code = f"{prefix}{today:%Y%m%d}-{random.randint(1000, 9999)}"
        if not (DefectRecord.objects.filter(code=code).exists()
                or InspectionOrder.objects.filter(code=code).exists()):
            return code
    return f"{prefix}{today:%Y%m%d}-{timezone.now():%H%M%S}"


def _reset_alarm_to_open(alarm):
    """工单取消时：来源告警回到未处理，由值班人员重新判断（不自动闭环）"""
    if alarm and alarm.status != "resolved":
        alarm.status = "open"
        alarm.save(update_fields=["status"])


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
        qs = (Alarm.objects.select_related("station", "device")
              .prefetch_related("dispatched_defects", "dispatched_inspections"))
        return _filtered(qs, self.request, {"station": "station_id", "status": "status",
                                            "level": "level", "alarm_id": "id"})

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
        """处理完成 -> 已处理，可补记处置措施"""
        alarm = self.get_object()
        alarm.status = "resolved"
        alarm.handler = request.data.get("handler", alarm.handler)
        alarm.handle_note = request.data.get("note", alarm.handle_note)
        alarm.handled_at = timezone.now()
        alarm.save(update_fields=["status", "handler", "handle_note", "handled_at"])
        return Response(AlarmSerializer(alarm).data)

    @action(detail=True, methods=["post"], url_path="dispatch")
    def dispatch_order(self, request, pk=None):
        """告警派单：生成消缺记录(type=defect)或巡检工单(type=inspection)

        注意：方法名不能叫 dispatch，否则会覆盖 View.dispatch() 请求分发入口。
        """
        alarm = self.get_object()

        if alarm.status == "resolved":
            return Response({"detail": "该告警已闭环，不允许派单"}, status=400)
        active = (alarm.dispatched_defects.exclude(status="cancelled").first()
                  or alarm.dispatched_inspections.exclude(status="cancelled").first())
        if active:
            return Response(
                {"detail": f"该告警已派单（{active.code}），不能重复派单"}, status=400)

        dtype = request.data.get("type")
        if dtype == "defect":
            level_map = {"info": "minor", "minor": "minor",
                         "major": "major", "critical": "critical"}
            order = DefectRecord.objects.create(
                source_alarm=alarm,
                station=alarm.station,
                device=alarm.device,
                code=_gen_code("XQ"),
                description=f"【告警派单】{alarm.title}\n{alarm.message}".strip(),
                level=request.data.get("level") or level_map.get(alarm.level, "minor"),
                reporter=request.data.get("reporter") or alarm.handler or "值班员",
                found_at=date.today(),
            )
            serializer = DefectRecordSerializer(order)
        elif dtype == "inspection":
            assignee = request.data.get("assignee")
            if not assignee:
                return Response({"detail": "生成巡检工单需指定执行人"}, status=400)
            order = InspectionOrder.objects.create(
                source_alarm=alarm,
                station=alarm.station,
                code=_gen_code("XJ"),
                title=f"【告警派单】{alarm.title}",
                order_type="fault",
                assignee=assignee,
                plan_date=request.data.get("plan_date") or date.today(),
            )
            serializer = InspectionOrderSerializer(order)
        else:
            return Response({"detail": "type 必须为 defect（消缺记录）或 inspection（巡检工单）"},
                            status=400)

        # 派单后告警进入处理中，等待工单闭环后由值班人员确认闭环
        alarm.status = "processing"
        alarm.save(update_fields=["status"])
        # 重新查询，避免 get_object() 的 prefetch 缓存导致 dispatch_info 为空
        alarm = Alarm.objects.get(pk=alarm.pk)
        return Response({"alarm": AlarmSerializer(alarm).data, "order": serializer.data},
                        status=201)


class InspectionOrderViewSet(viewsets.ModelViewSet):
    serializer_class = InspectionOrderSerializer

    def get_queryset(self):
        qs = InspectionOrder.objects.select_related("station", "source_alarm")
        return _filtered(qs, self.request, {"station": "station_id", "status": "status",
                                            "type": "order_type", "alarm": "source_alarm"})

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
        if order.status == "done":
            return Response({"detail": "已完成的工单不能取消"}, status=400)
        order.status = "cancelled"
        order.save(update_fields=["status"])
        _reset_alarm_to_open(order.source_alarm)
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
        qs = DefectRecord.objects.select_related("station", "device", "source_alarm")
        return _filtered(qs, self.request, {"station": "station_id", "status": "status",
                                            "level": "level", "alarm": "source_alarm"})

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

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """作废消缺记录：来源告警回到未处理"""
        defect = self.get_object()
        if defect.status == "resolved":
            return Response({"detail": "已消缺的记录不能作废"}, status=400)
        defect.status = "cancelled"
        defect.save(update_fields=["status"])
        _reset_alarm_to_open(defect.source_alarm)
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
