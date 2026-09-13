# ---------- 前端构建 ----------
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- 后端 + 静态托管 ----------
FROM python:3.11-slim
WORKDIR /app
# 保持与仓库一致的目录结构：backend/ 与 frontend/dist 为同级，
# 使 settings.py 中 BASE_DIR.parent/"frontend"/"dist" 能正确解析
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY --from=frontend /build/dist frontend/dist
WORKDIR /app/backend
ENV DJANGO_DEBUG=0
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD python manage.py migrate && \
    python manage.py seed && \
    python manage.py runserver 0.0.0.0:8000
