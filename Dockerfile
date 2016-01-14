FROM python:2.7

RUN \
  cd /tmp && \
  curl -sL https://deb.nodesource.com/setup_5.x | bash - && \
  apt-get install --yes nodejs

RUN \
  npm install -g gulp && \
  npm install -g bower

RUN apt-get update && apt-get -y install python-gdal gdal-bin libgdal-dev libgdal1h libgdal1-dev libxml2-dev libxslt-dev python-dev xmlsec1

ENV CPLUS_INCLUDE_PATH /usr/include/gdal
ENV C_INCLUDE_PATH /usr/include/gdal
ENV PYTHONUNBUFFERED 1
RUN mkdir /code

ADD EquiTrack /code/
RUN pip install -r /code/requirements/production.txt

COPY frontend /code/frontend/
WORKDIR /code/frontend/
RUN sh /code/frontend/build.sh

WORKDIR /code/
ENV DJANGO_SETTINGS_MODULE EquiTrack.settings.production
RUN python manage.py collectstatic --noinput

# Start everything
ENV PORT 8080
EXPOSE $PORT
ENV C_FORCE_ROOT true
CMD honcho start
