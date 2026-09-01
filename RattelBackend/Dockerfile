# Build stage
FROM python:3.14.2-slim AS builder
WORKDIR /app

# Configure pip mirror first
#RUN pip config --user set global.index https://pypi.devneeds.ir/simple/ \
#    && pip config --user set global.index-url https://pypi.devneeds.ir/simple/ \
#    && pip config --user set global.trusted-host devneeds.ir

# --- Apt Mirror Configuration and Installation of lsb-release ---
# 1. Manually create the sources.list with the mirror.
# 2. Then run apt-get update (which will use the mirror) and install lsb-release.
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    libpq-dev \
    pkg-config \
    libdbus-1-dev \
    libglib2.0-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.14.2-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

## Configure pip mirror first for the runtime stage as well
#RUN pip config --user set global.index https://pypi.devneeds.ir/simple/ \
#    && pip config --user set global.index-url https://pypi.devneeds.ir/simple/ \
#    && pip config --user set global.trusted-host devneeds.ir

# --- Apt Mirror Configuration and Installation of lsb-release ---
# 1. Manually create the sources.list with the mirror.
# 2. Then run apt-get update (which will use the mirror) and install lsb-release.
RUN apt-get update && \
    apt-get install -y \
    postgresql-client \
    curl \
    libwebp7 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . /app/
RUN mkdir -p /app/logs /app/static /app/staticfiles /app/media
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
