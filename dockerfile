FROM python:3.9.7-buster
ADD . /manymanager
WORKDIR /manymanager
RUN pip3 install -r requirements.txt
ENTRYPOINT flask run --host=0.0.0.0 --port 8000
EXPOSE 8000