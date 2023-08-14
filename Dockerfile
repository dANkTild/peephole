FROM python:3.9-slim-buster
LABEL authors="enard"

WORKDIR /app

VOLUME /app/database
VOLUME /app/media
EXPOSE 5000

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install ffmpeg  -y

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]