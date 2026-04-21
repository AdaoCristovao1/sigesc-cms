FROM python:3.11-slim

# Instalar dependências do sistema (ESSENCIAL)
RUN apt-get update && apt-get install -y \
    gcc \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /tmp/requirements.txt

COPY . /app

CMD python manage.py migrate --noinput && \
    python manage.py loaddata dados.json || true && \
    gunicorn sigesc.wsgi:application --bind 0.0.0.0:$PORT