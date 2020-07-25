FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install -y python3 python3-pip
# RUN apt-get install -y pandoc

ADD app /app
ADD requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt
RUN python3 setup.py develop