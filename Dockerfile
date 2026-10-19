FROM maven:3.9-eclipse-temurin-17 AS api-build
WORKDIR /build
COPY api/pom.xml ./pom.xml
RUN mvn -B dependency:go-offline
COPY api/src ./src
RUN mvn -B package

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_DEBUG=0
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY web/requirements.txt /app/web/requirements.txt
RUN pip install --no-cache-dir -r /app/web/requirements.txt
COPY --from=api-build /build/target/dispensalud-api-0.1.0-SNAPSHOT.jar /app/api.jar
COPY web /app/web
COPY deploy /app/deploy
WORKDIR /app/web
RUN DJANGO_DEBUG=1 DJANGO_SECRET_KEY=static-build-only-not-a-runtime-secret python manage.py collectstatic --noinput && useradd --create-home app && chown -R app:app /app
USER app
CMD ["python", "/app/deploy/start.py"]
