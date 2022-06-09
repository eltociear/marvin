FROM python:3.10-slim

ADD . marvin

EXPOSE 8080

RUN pip install -e ./marvin

CMD marvin
