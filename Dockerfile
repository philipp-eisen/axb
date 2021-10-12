FROM python:3.8-alpine3.11

COPY . /app
WORKDIR /app

RUN pip install slack_sdk requests 

CMD python main.py
