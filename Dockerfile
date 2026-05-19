FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline
COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim AS backend-base
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


FROM backend-base AS backend-test
COPY backend/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY backend/ ./

# backend-dev has no COPY — it relies on the volume mount in docker-compose.yml.
# Building this stage standalone produces a broken image; use docker compose up instead.
FROM backend-base AS backend-dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


FROM backend-base AS runtime
COPY backend/ ./
COPY --from=frontend-builder /frontend/dist ./static
RUN mkdir -p /data/chroma /data/uploads
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
