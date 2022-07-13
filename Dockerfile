FROM python:3.9 AS app

RUN pip install --upgrade pip && pip install pipenv
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates nginx xmlsec1 libxmlsec1-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /opt/app
WORKDIR /opt/app

RUN pip install gunicorn

ENV PYTHONPATH=/opt/app/
ADD Pipfile /opt/app/
ADD Pipfile.lock /opt/app/
RUN pipenv install --system

ADD manage.py /opt/app/
ADD jpnic_gui/ /opt/app/jpnic_gui/
#ADD jpnic_gui/production_settings.py /opt/app/jpnic_gui/settings.py


# NGINX
RUN python manage.py collectstatic --noinput
RUN ln -s /opt/app/static /var/www/html/static
ADD files/nginx.conf /etc/nginx/nginx.conf
ADD files/default.conf /etc/nginx/sites-enabled/default

EXPOSE 80

ADD files/entrypoint.sh /opt/app/
CMD ["bash", "-xe", "/opt/app/entrypoint.sh"]
