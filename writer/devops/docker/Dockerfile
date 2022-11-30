FROM python:3.7.15-alpine3.17

WORKDIR /home

ADD requirements.txt .
RUN python3 -m pip install -r requirements.txt
ADD src src
ADD config config
ADD runner.py runner.py
CMD python3 -u runner.py
