FROM python:3.7

ADD . marvin

EXPOSE 8080

RUN pip install ./marvin

CMD marvin
