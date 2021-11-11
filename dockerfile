FROM python:3.9.7-buster
ADD . /manymanager
WORKDIR /manymanager
RUN pip install --upgrade pip && pip install -r requirements.txt
EXPOSE 8000