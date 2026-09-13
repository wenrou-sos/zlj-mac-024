"""生成样例数据：python manage.py seed [--force]"""
import math
import random
from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (Alarm, CleaningPlan, DefectRecord, Device,
                         InspectionOrder, PowerData, Station)

STATIONS = [
    dict(name="格尔木戈壁光伏电站", code="GEM01", city="青海·格尔木", capacity_kwp=50000,
         owner="华能新能源", contact="0979-8451200", grid_date=date(2019, 6, 28),
         description="位于格尔木光伏产业园，采用固定式支架与组串式逆变器。"),
    dict(name="中卫沙漠光伏电站", code="ZW02", city="宁夏·中卫", capacity_kwp=80000,
         owner="国电投宁夏公司", contact="0955-7023300", grid_date=date(2020, 12, 15),
         description="沙漠治理与光伏互补项目，配套防风固沙设施。"),
    dict(name="德州平原光伏电站", code="DZ03", city="山东·德州", capacity_kwp=30000,
         owner="山东能源集团", contact="0534-2688100", grid_date=date(2021, 5, 20),
         description="平原农光互补电站，板上发电、板下种植。"),
    dict(name="盐城滩涂光伏电站", code="YC04", city="江苏·盐城", capacity_kwp=60000,
         owner="江苏国信", contact="0515-8836600", grid_date=date(2020, 9, 1),
         description="沿海滩涂渔光互补项目，需重点关注盐雾腐蚀与组件清洗。"),
    dict(name="湖州山地光伏电站", code="HZ05", city="浙江·湖州", capacity_kwp=20000,
         owner="正泰新能源", contact="0572-2108800", grid_date=date(2022, 3, 18),
         description="山地电站，地形起伏大，组串失配与遮挡问题需重点巡检。"),
    dict(name="梅州分布式光伏电站", code="MZ06", city="广东·梅州", capacity_kwp=12000,
         owner="南网综合能源", contact="0753-2289900", grid_date=date(2023, 1, 10),
         description="县域屋顶分布式集群，含 86 个子阵统一接入监控。"),
]

INVERTER_MODELS = ["SUN2000-196KTL", "SG250HX", "GCI-230K-EHV"]
WORKERS = ["张伟", "李强", "王芳", "刘洋", "陈杰", "赵磊"]

ALARM_TEMPLATES = [
    ("inverter", "逆变器直流侧绝缘阻抗低", "major", "绝缘阻抗降至 {v}kΩ，低于阈值 100kΩ，请检查直流电缆与接头。"),
    ("inverter", "逆变器交流过压保护动作", "critical", "电网电压越上限，逆变器脱网保护，需核查箱变分接头档位。"),
    ("inverter", "逆变器模块温度异常", "minor", "IGBT 模块温度 {v}℃，超过告警阈值，请检查散热风扇。"),
    ("combiner", "汇流箱支路电流异常", "major", "第 {v} 路电流为 0，疑似组串开路或熔断器熔断。"),
    ("combiner", "汇流箱通讯中断", "info", "RS485 通讯超时，请检查通讯模块与接线。"),
    ("transformer", "箱变油温过高", "major", "顶层油温 {v}℃，请检查冷却系统与负载率。"),
    ("monitor", "辐照仪数据异常", "info", "辐照数据连续 30 分钟无变化，疑似传感器故障。"),
    ("meter", "关口表计量偏差告警", "minor", "关口表与逆变器累计电量偏差超过 2%，请核对计量回路。"),
    ("inverter", "逆变器频繁启停", "minor", "弱光条件下 1 小时内启停 {v} 次，建议优化启机阈值。"),
    ("combiner", "组串接地故障", "critical", "检测到直流侧对地故障，漏电流 {v}mA，请立即排查。"),
]

DEFECT_TEMPLATES = [
    "逆变器散热风扇异响，轴承磨损需更换",
    "汇流箱熔断器熔断，备件更换",
    "组件表面热斑，EL 检测确认电池片隐裂",
    "MC4 连接器烧蚀，接触电阻过大",
    "直流电缆被老鼠咬破，绝缘层破损",
    "支架螺栓松动，需按力矩复紧",
    "箱变低压侧断路器触头发热",
    "组件玻璃破损（冰雹击打）",
    "通讯管理机死机，重启后恢复并升级固件",
    "组串式逆变器风扇卡死，更换风扇模组",
]

CLEAN_AREAS = ["一期 A 区方阵", "一期 B 区方阵", "二期 C 区方阵", "全场组件", "东区 1-20 号方阵", "西区 21-40 号方阵"]


def seasonal_hours(d: date) -> float:
    """等效小时数的季节因子：夏季高、冬季低"""
    return 1.0 + 0.28 * math.cos((d.timetuple().tm_yday - 172) / 365 * 2 * math.pi)


class Command(BaseCommand):
    help = "生成光伏电站样例数据"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="清空已有业务数据后重新生成")

    def handle(self, *args, **opts):
        if Station.objects.exists():
            if not opts["force"]:
                self.stdout.write(self.style.WARNING(
                    "已存在数据，跳过。使用 --force 清空后重新生成。"))
                return
            for m in (PowerData, Alarm, InspectionOrder, CleaningPlan, DefectRecord,
                      Device, Station):
                m.objects.all().delete()
            self.stdout.write("已清空旧数据。")

        rng = random.Random(20260913)
        today = date.today()
        stations = []

        # ---- 电站与设备 ----
        for i, cfg in enumerate(STATIONS):
            st = Station.objects.create(**cfg)
            stations.append(st)
            devices = []
            n_inv = max(3, int(cfg["capacity_kwp"] / 8000))
            for k in range(1, n_inv + 1):
                devices.append(Device(station=st, name=f"逆变器#{k:02d}", device_type="inverter",
                                      model=rng.choice(INVERTER_MODELS),
                                      serial_no=f"INV{st.code}{k:03d}",
                                      install_date=cfg["grid_date"]))
            for k in range(1, 5):
                devices.append(Device(station=st, name=f"汇流箱#{k:02d}", device_type="combiner",
                                      model="CBX-16", serial_no=f"CB{st.code}{k:03d}",
                                      install_date=cfg["grid_date"]))
            devices.append(Device(station=st, name="箱变#01", device_type="transformer",
                                  model="ZGS11-2000/35", install_date=cfg["grid_date"]))
            devices.append(Device(station=st, name="关口电能表", device_type="meter",
                                  model="DTSD341", install_date=cfg["grid_date"]))
            devices.append(Device(station=st, name="环境监测仪", device_type="monitor",
                                  model="SPN1-W", install_date=cfg["grid_date"]))
            Device.objects.bulk_create(devices)

        # ---- 120 天发电数据 ----
        bulk = []
        for st in stations:
            base_hours = 4.3 if st.capacity_kwp >= 30000 else 3.8  # 小电站含分布式，略低
            for d in range(120):
                day = today - timedelta(days=d)
                weather = 1.0
                r = rng.random()
                if r < 0.12:
                    weather = rng.uniform(0.35, 0.65)   # 阴雨
                elif r < 0.3:
                    weather = rng.uniform(0.7, 0.9)     # 多云
                hours = base_hours * seasonal_hours(day) * weather * rng.uniform(0.94, 1.04)
                energy = round(st.capacity_kwp * hours, 1)
                bulk.append(PowerData(
                    station=st, date=day, energy_kwh=energy,
                    peak_power_kw=round(st.capacity_kwp * rng.uniform(0.78, 0.92), 1),
                    equivalent_hours=round(hours, 2),
                    pr=round(rng.uniform(78, 88), 1),
                    irradiance=round(hours * rng.uniform(0.95, 1.05), 2),
                ))
        PowerData.objects.bulk_create(bulk)

        # ---- 告警 ----
        alarms = []
        for st in stations:
            devs = list(st.devices.all())
            for _ in range(rng.randint(4, 7)):
                tpl = rng.choice(ALARM_TEMPLATES)
                dtype, title, level, msg = tpl
                dev = rng.choice([d for d in devs if d.device_type == dtype] or devs)
                created = timezone.now() - timedelta(
                    days=rng.randint(0, 13), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
                status = rng.choices(["open", "processing", "resolved"], weights=[3, 2, 5])[0]
                a = Alarm(station=st, device=dev, level=level, title=title,
                          message=msg.format(v=rng.randint(20, 220)), status=status,
                          handler=rng.choice(WORKERS) if status != "open" else "",
                          handled_at=created + timedelta(hours=rng.randint(1, 30))
                          if status == "resolved" else None)
                alarms.append(a)
        Alarm.objects.bulk_create(alarms)
        # 回填告警时间为随机过去时间（bulk_create 中 auto_now_add 统一为当前时间）
        for a in Alarm.objects.all():
            a.created_at = timezone.now() - timedelta(days=rng.randint(0, 13),
                                                      hours=rng.randint(0, 23))
            if a.status == "resolved":
                a.handled_at = a.created_at + timedelta(hours=rng.randint(1, 30))
            a.save(update_fields=["created_at", "handled_at"])

        # 让部分设备处于告警/故障状态，与未处理告警呼应
        for st in stations:
            open_devs = {a.device_id for a in st.alarms.exclude(status="resolved") if a.device_id}
            for did in open_devs:
                Device.objects.filter(id=did).update(status=rng.choice(["warning", "fault"]))

        # ---- 巡检工单 ----
        seq = 1
        for st in stations:
            for _ in range(rng.randint(2, 3)):
                status = rng.choices(["pending", "in_progress", "done"], weights=[3, 1, 4])[0]
                plan = today + timedelta(days=rng.randint(-20, 10))
                order = InspectionOrder.objects.create(
                    station=st, code=f"XJ{plan:%Y%m%d}-{seq:03d}",
                    title=f"{st.name}{rng.choice(['季度', '月度', '雨后专项', '节前'])}巡检",
                    order_type=rng.choice(["regular", "regular", "special", "fault"]),
                    assignee=rng.choice(WORKERS), status=status, plan_date=plan,
                    result="设备运行正常，未发现重大隐患。" if status == "done" else "",
                    finished_at=timezone.now() - timedelta(days=rng.randint(0, 5))
                    if status == "done" else None)
                seq += 1

        # ---- 清洗计划 ----
        seq = 1
        for st in stations:
            for _ in range(rng.randint(1, 2)):
                status = rng.choices(["planned", "in_progress", "done"], weights=[4, 1, 3])[0]
                plan = today + timedelta(days=rng.randint(-15, 20))
                CleaningPlan.objects.create(
                    station=st, code=f"QX{plan:%Y%m%d}-{seq:03d}",
                    area=rng.choice(CLEAN_AREAS), plan_date=plan,
                    executor=rng.choice(["清洗一班", "清洗二班", "外委清洗队"]),
                    status=status,
                    note="采用机器人干扫+水车冲洗结合。" if status == "done" else "",
                    finished_at=timezone.now() - timedelta(days=rng.randint(0, 3))
                    if status == "done" else None)
                seq += 1

        # ---- 消缺记录 ----
        seq = 1
        for st in stations:
            devs = list(st.devices.all())
            for _ in range(rng.randint(2, 4)):
                status = rng.choices(["open", "processing", "resolved"], weights=[3, 2, 5])[0]
                found = today - timedelta(days=rng.randint(0, 40))
                DefectRecord.objects.create(
                    station=st, device=rng.choice(devs),
                    code=f"XQ{found:%Y%m%d}-{seq:03d}",
                    description=rng.choice(DEFECT_TEMPLATES),
                    level=rng.choices(["minor", "major", "critical"], weights=[5, 3, 1])[0],
                    status=status, reporter=rng.choice(WORKERS),
                    handler=rng.choice(WORKERS) if status != "open" else "",
                    found_at=found,
                    resolved_at=timezone.now() - timedelta(days=rng.randint(0, 10))
                    if status == "resolved" else None,
                    solution="已处理完毕，设备恢复正常运行。" if status == "resolved" else "")
                seq += 1

        self.stdout.write(self.style.SUCCESS(
            f"样例数据生成完成：电站 {Station.objects.count()} 座，"
            f"设备 {Device.objects.count()} 台，发电数据 {PowerData.objects.count()} 条，"
            f"告警 {Alarm.objects.count()} 条，工单 {InspectionOrder.objects.count()} 张，"
            f"清洗计划 {CleaningPlan.objects.count()} 项，消缺 {DefectRecord.objects.count()} 条。"))
