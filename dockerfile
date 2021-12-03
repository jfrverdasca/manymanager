FROM debian:10
ARG DEBIAN_FRONTEND=noninteractive
ADD . /var/www/manymanager
WORKDIR /var/www/manymanager
RUN apt-get update && apt-get install -y python3.7 python3-pip \
    python3.7-dev libpq-dev gcc libffi-dev apache2 libapache2-mod-wsgi-py3 && \
    pip3 install -r requirements.txt && \
    service apache2 restart
ENTRYPOINT apachectl -D FOREGROUND