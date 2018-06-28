FROM continuumio/miniconda3:latest

ADD . marvin

RUN cd marvin && conda env create

#RUN source activate marvin \
#    && pip install . \
#    && marvin
RUN bash -c "source activate marvin && pip install ./marvin"

CMD bash -c "source activate marvin && marvin"
