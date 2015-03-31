FROM python:2.7
RUN apt-get update && apt-get -y install python-gdal gdal-bin libgdal-dev libgdal1h libgdal1-dev libxml2-dev libxslt-dev python-dev
ENV CPLUS_INCLUDE_PATH /usr/include/gdal
ENV C_INCLUDE_PATH /usr/include/gdal
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN pip install -r requirements.txt
ENV DJANGO_SETTINGS_MODULE EquiTrack.settings.production
RUN python EquiTrack/manage.py collectstatic --noinput
# Start everything
EXPOSE 8080
ENTRYPOINT newrelic-admin run-program python EquiTrack/manage.py run_gunicorn -b "0.0.0.0:8080" -w 3 --timeout=1200
