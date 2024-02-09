# Tony
FROM ubuntu:jammy
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -yq install python3-pip

COPY requirements.txt /model/
RUN pip3 install -r /model/requirements.txt


COPY aki_detector.py /model/
COPY aki_model.json /model/
COPY aki.csv /model/
COPY app.py /model/
COPY data_processor.py /model/
COPY history.csv /model/
COPY hl7_processor.py /model/
COPY listener.py /model/
COPY pager_system.py /model/
COPY f3_evaluation.py /model/

RUN chmod +x /model/app.py
EXPOSE 8440
EXPOSE 8441

CMD /model/app.py --mllp=$MLLP_ADDRESS --pager=$PAGER_ADDRESS