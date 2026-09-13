from django.db import models


class Station(models.Model):
    """光伏电站"""

    STATUS_CHOICES = [
        ("running", "运行正常"),
        ("maintenance", "检修中"),
        ("fault", "故障"),
    ]

    name = models.CharField("电站名称", max_length=100)
    code = models.CharField("电站编码", max_length=30, unique=True)
    city = models.CharField("所在地区", max_length=100)
    capacity_kwp = models.FloatField("装机容量(kWp)")
    status = models.CharField("运行状态", max_length=20, choices=STATUS_CHOICES, default="running")
    grid_date = models.DateField("并网日期", null=True, blank=True)
    owner = models.CharField("业主单位", max_length=100, blank=True, default="")
    contact = models.CharField("联系电话", max_length=30, blank=True, default="")
    description = models.TextField("简介", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "电站"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.name


class Device(models.Model):
    """电站设备（逆变器/汇流箱/箱变/电表/环境监测仪）"""

    TYPE_CHOICES = [
        ("inverter", "逆变器"),
        ("combiner", "汇流箱"),
        ("transformer", "箱式变压器"),
        ("meter", "电能表"),
        ("monitor", "环境监测仪"),
    ]
    STATUS_CHOICES = [
        ("normal", "正常"),
        ("warning", "告警"),
        ("fault", "故障"),
        ("offline", "离线"),
    ]

    station = models.ForeignKey(Station, related_name="devices", on_delete=models.CASCADE, verbose_name="所属电站")
    name = models.CharField("设备名称", max_length=100)
    device_type = models.CharField("设备类型", max_length=20, choices=TYPE_CHOICES)
    model = models.CharField("型号", max_length=60, blank=True, default="")
    serial_no = models.CharField("序列号", max_length=60, blank=True, default="")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="normal")
    install_date = models.DateField("安装日期", null=True, blank=True)

    class Meta:
        verbose_name = "设备"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return f"{self.station.name}-{self.name}"


class PowerData(models.Model):
    """电站日发电数据"""

    station = models.ForeignKey(Station, related_name="power_data", on_delete=models.CASCADE, verbose_name="电站")
    date = models.DateField("日期")
    energy_kwh = models.FloatField("发电量(kWh)")
    peak_power_kw = models.FloatField("峰值功率(kW)", default=0)
    equivalent_hours = models.FloatField("等效利用小时(h)", default=0)
    pr = models.FloatField("系统效率PR(%)", default=0)
    irradiance = models.FloatField("水平面辐照量(kWh/m²)", default=0)

    class Meta:
        verbose_name = "发电数据"
        verbose_name_plural = verbose_name
        unique_together = ("station", "date")
        ordering = ["-date"]
        indexes = [models.Index(fields=["station", "date"])]

    def __str__(self):
        return f"{self.station.code} {self.date} {self.energy_kwh:.0f}kWh"


class Alarm(models.Model):
    """异常告警"""

    LEVEL_CHOICES = [
        ("info", "提示"),
        ("minor", "一般"),
        ("major", "严重"),
        ("critical", "紧急"),
    ]
    STATUS_CHOICES = [
        ("open", "未处理"),
        ("processing", "处理中"),
        ("resolved", "已处理"),
    ]

    station = models.ForeignKey(Station, related_name="alarms", on_delete=models.CASCADE, verbose_name="电站")
    device = models.ForeignKey(Device, related_name="alarms", on_delete=models.SET_NULL,
                               null=True, blank=True, verbose_name="关联设备")
    level = models.CharField("告警级别", max_length=20, choices=LEVEL_CHOICES, default="minor")
    title = models.CharField("告警标题", max_length=120)
    message = models.TextField("告警详情", blank=True, default="")
    status = models.CharField("处理状态", max_length=20, choices=STATUS_CHOICES, default="open")
    handler = models.CharField("处理人", max_length=30, blank=True, default="")
    handle_note = models.TextField("处置措施", blank=True, default="")
    created_at = models.DateTimeField("告警时间", auto_now_add=True)
    handled_at = models.DateTimeField("处理时间", null=True, blank=True)

    class Meta:
        verbose_name = "告警"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_level_display()}] {self.title}"


class InspectionOrder(models.Model):
    """巡检工单"""

    TYPE_CHOICES = [
        ("regular", "定期巡检"),
        ("special", "专项巡检"),
        ("fault", "故障巡检"),
    ]
    STATUS_CHOICES = [
        ("pending", "待执行"),
        ("in_progress", "执行中"),
        ("done", "已完成"),
        ("cancelled", "已取消"),
    ]

    station = models.ForeignKey(Station, related_name="inspections", on_delete=models.CASCADE, verbose_name="电站")
    source_alarm = models.ForeignKey(Alarm, related_name="dispatched_inspections",
                                     on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="来源告警")
    code = models.CharField("工单编号", max_length=30, unique=True)
    title = models.CharField("工单标题", max_length=120)
    order_type = models.CharField("巡检类型", max_length=20, choices=TYPE_CHOICES, default="regular")
    assignee = models.CharField("执行人", max_length=30)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="pending")
    plan_date = models.DateField("计划日期")
    finished_at = models.DateTimeField("完成时间", null=True, blank=True)
    result = models.TextField("巡检结果", blank=True, default="")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "巡检工单"
        verbose_name_plural = verbose_name
        ordering = ["-plan_date", "-id"]

    def __str__(self):
        return f"{self.code} {self.title}"


class CleaningPlan(models.Model):
    """组件清洗计划"""

    STATUS_CHOICES = [
        ("planned", "待执行"),
        ("in_progress", "进行中"),
        ("done", "已完成"),
        ("cancelled", "已取消"),
    ]

    station = models.ForeignKey(Station, related_name="cleanings", on_delete=models.CASCADE, verbose_name="电站")
    code = models.CharField("计划编号", max_length=30, unique=True)
    area = models.CharField("清洗区域", max_length=100)
    plan_date = models.DateField("计划日期")
    executor = models.CharField("执行人/班组", max_length=50)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="planned")
    finished_at = models.DateTimeField("完成时间", null=True, blank=True)
    note = models.TextField("备注", blank=True, default="")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "清洗计划"
        verbose_name_plural = verbose_name
        ordering = ["-plan_date", "-id"]

    def __str__(self):
        return f"{self.code} {self.station.name}-{self.area}"


class DefectRecord(models.Model):
    """消缺记录"""

    LEVEL_CHOICES = [
        ("minor", "一般"),
        ("major", "严重"),
        ("critical", "危急"),
    ]
    STATUS_CHOICES = [
        ("open", "待消缺"),
        ("processing", "消缺中"),
        ("resolved", "已消缺"),
        ("cancelled", "已作废"),
    ]

    station = models.ForeignKey(Station, related_name="defects", on_delete=models.CASCADE, verbose_name="电站")
    source_alarm = models.ForeignKey(Alarm, related_name="dispatched_defects",
                                     on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="来源告警")
    device = models.ForeignKey(Device, related_name="defects", on_delete=models.SET_NULL,
                               null=True, blank=True, verbose_name="关联设备")
    code = models.CharField("缺陷编号", max_length=30, unique=True)
    description = models.TextField("缺陷描述")
    level = models.CharField("缺陷级别", max_length=20, choices=LEVEL_CHOICES, default="minor")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="open")
    reporter = models.CharField("发现人", max_length=30)
    handler = models.CharField("消缺人", max_length=30, blank=True, default="")
    found_at = models.DateField("发现日期")
    resolved_at = models.DateTimeField("消缺时间", null=True, blank=True)
    solution = models.TextField("处理措施", blank=True, default="")
    created_at = models.DateTimeField("登记时间", auto_now_add=True)

    class Meta:
        verbose_name = "消缺记录"
        verbose_name_plural = verbose_name
        ordering = ["-found_at", "-id"]

    def __str__(self):
        return f"{self.code} {self.description[:20]}"
