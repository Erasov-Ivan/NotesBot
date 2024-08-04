# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster as base

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN rm requirements.txt

COPY . .


ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
