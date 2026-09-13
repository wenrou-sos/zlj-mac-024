from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django.template.exceptions import TemplateDoesNotExist
from django.urls import include, path, re_path

# 前端未构建时的引导页（避免直接 500）
FRONTEND_MISSING_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>光伏运维平台 - 前端未构建</title>
  <style>
    body { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #0d2240;
           color: #e8eef7; display: flex; align-items: center; justify-content: center;
           min-height: 100vh; margin: 0; }
    .box { max-width: 620px; padding: 40px; }
    h1 { font-size: 24px; } h1 span { color: #f7c948; }
    pre { background: rgba(0,0,0,.35); padding: 16px 20px; border-radius: 8px; line-height: 1.9;
          font-size: 14px; overflow-x: auto; }
    code { background: rgba(255,255,255,.12); padding: 2px 8px; border-radius: 4px; }
    a { color: #79b8ff; }
    .ok { color: #7ee2a8; }
  </style>
</head>
<body>
  <div class="box">
    <h1><span>☀</span> 光伏电站智能运维平台</h1>
    <p class="ok">✔ 后端 API 运行正常（<a href="/api/stations/">/api/stations/</a> 可访问）</p>
    <p>✘ 前端页面尚未构建，请执行：</p>
    <pre>cd frontend
npm install
npm run build</pre>
    <p>构建完成后刷新本页即可。开发模式可运行 <code>npm run dev</code>
       并访问 <code>http://127.0.0.1:5173</code>。</p>
  </div>
</body>
</html>"""


def spa(request):
    """SPA 入口：前端已构建则返回 index.html，否则返回构建引导页"""
    try:
        return render(request, "index.html")
    except TemplateDoesNotExist:
        return HttpResponse(FRONTEND_MISSING_HTML, content_type="text/html; charset=utf-8")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    # 其余路径全部交给前端 SPA（Vue Router history 模式）
    re_path(r"^(?!api/|admin/|static/).*$", spa),
]
