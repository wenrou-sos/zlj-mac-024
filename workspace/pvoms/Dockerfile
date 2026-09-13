FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend /app/frontend/dist /app/frontend/dist
ENV DJANGO_DEBUG=0
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD python manage.py migrate && \
    python manage.py seed && \
    python manage.py runserver 0.0.0.0:8000
