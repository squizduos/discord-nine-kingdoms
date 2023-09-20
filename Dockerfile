FROM python:3.9-alpine3.15

RUN apk add --no-cache libffi python3-dev ffmpeg libopusenc

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./app /app

ENTRYPOINT ["python", "/app/main.py"]
