FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Зависимости для Postgres
RUN apt-get update && apt-get install -y libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r ./requirements.txt
COPY . ./
RUN python3 ./manage.py collectstatic --no-input
RUN python3 ./manage.py migrate --no-input
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
