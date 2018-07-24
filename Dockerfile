FROM python:3.6

ADD . marvin

EXPOSE 8080

RUN pip install ./marvin

CMD marvin
