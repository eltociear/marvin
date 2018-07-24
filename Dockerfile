FROM python:3.6

ADD . marvin

RUN pip install ./marvin

CMD marvin
