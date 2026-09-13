# 光伏电站智能运维平台（PVOMS）

面向光伏电站的运维管理系统：集中展示各电站发电数据与设备状态，覆盖
**异常告警、巡检工单、清洗计划、消缺记录** 全流程闭环管理。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Element Plus + ECharts + Vue Router |
| 后端 | Django 5 + Django REST Framework |
| 数据库 | PostgreSQL（生产）/ SQLite（本地演示，零配置） |

## 功能模块

- **运行总览**：电站规模、今日/本月/本年发电量、30 天发电趋势、设备状态分布、告警级别分布、待办事项
- **电站管理**：电站卡片总览 → 电站详情（日发电/PR 曲线、今日逐时出力、设备清单、本站告警）
- **异常告警**：级别（提示/一般/严重/紧急）× 状态（未处理/处理中/已处理）流转闭环
- **巡检工单**：定期/专项/故障巡检，新建 → 执行 → 完成（填写结果）/取消
- **清洗计划**：方阵级清洗计划排程与执行跟踪
- **消缺记录**：缺陷登记（关联设备）→ 消缺中 → 已消缺闭环

内置 6 座样例电站（青海/宁夏/山东/江苏/浙江/广东）、74 台设备、120 天发电数据及配套告警/工单/清洗/消缺数据。

## 快速开始（本地，SQLite 零配置）

```bash
# 1. 后端
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed          # 生成样例数据（--force 可重置）
python manage.py runserver     # http://127.0.0.1:8000

# 2. 前端（另开终端，二选一）
cd frontend
npm install
npm run build                  # 方式一：构建后由 Django 托管，访问 :8000
npm run dev                    # 方式二：开发热更新，访问 :5173（已配置 /api 代理）
```

## Docker（PostgreSQL 一键部署）

```bash
docker compose up --build
# 访问 http://localhost:8000 ，自动建库、迁移并注入样例数据
```

## 切换 PostgreSQL（不用 Docker 时）

设置环境变量即可，无需改代码：

```bash
export DATABASE_URL=postgres://user:password@host:5432/pvoms
python manage.py migrate && python manage.py seed
```

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/overview/` | 驾驶舱总览聚合数据 |
| GET | `/api/stations/` | 电站列表（含今日发电/活跃告警/设备数） |
| GET | `/api/stations/{id}/power/?days=30` | 日发电序列 |
| GET | `/api/stations/{id}/power_hourly/` | 今日逐时出力曲线 |
| GET | `/api/stations/{id}/devices/` | 电站设备清单 |
| GET/POST/PATCH | `/api/alarms/` | 告警查询/创建（支持 station/level/status 过滤） |
| POST | `/api/alarms/{id}/start/` `/resolve/` | 告警处理流转 |
| GET/POST | `/api/inspections/` | 巡检工单 |
| POST | `/api/inspections/{id}/start/` `/complete/` `/cancel/` | 工单流转 |
| GET/POST | `/api/cleanings/` | 清洗计划（流转同上） |
| GET/POST | `/api/defects/` | 消缺记录 |
| POST | `/api/defects/{id}/start/` `/resolve/` | 消缺流转 |

## 目录结构

```
pvoms/
├── backend/
│   ├── config/            # Django 配置（DATABASE_URL 支持 PostgreSQL）
│   └── core/
│       ├── models.py      # 电站/设备/发电数据/告警/工单/清洗/消缺
│       ├── views.py       # DRF ViewSet + 总览聚合
│       └── management/commands/seed.py   # 样例数据
├── frontend/
│   └── src/
│       ├── views/         # 总览/电站/告警/工单/清洗/消缺页面
│       ├── utils/dict.js  # 状态字典
│       └── utils/chart.js # ECharts 组合式封装
├── Dockerfile
└── docker-compose.yml     # web + postgres
```
