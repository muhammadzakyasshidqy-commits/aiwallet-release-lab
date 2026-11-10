FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AIWALLET_DATA_DIR=/data
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir '.[web]' && useradd --create-home --uid 10001 releaselab && mkdir -p /data && chown -R releaselab:releaselab /data /app
USER releaselab
EXPOSE 7860
VOLUME ["/data"]
CMD ["uvicorn", "aiwallet_release_lab.web:app", "--host", "0.0.0.0", "--port", "7860", "--no-access-log"]
