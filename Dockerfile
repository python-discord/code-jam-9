FROM python:latest

MAINTAINER zesty zombies

RUN apt-get update -y && apt-get install -y python3-pip python-dev

COPY /requirements.txt /app/requirements.txt

WORKDIR /app
RUN python --version
RUN pip3 install -r /app/requirements.txt
run pip3 list
COPY / /app

CMD [ "python3", "./backend/server.py"]

