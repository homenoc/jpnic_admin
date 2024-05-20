FROM python:3.12 AS app

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
ADD requirements.txt /opt/app/requirements.txt
RUN pip install -r requirements.txt

ADD manage.py /opt/app/
ADD jpnic_admin/ /opt/app/jpnic_admin/
#ADD jpnic_admin/production_settings.py /opt/app/jpnic_admin/settings.py


# NGINX
RUN python manage.py collectstatic --noinput
RUN ln -s /opt/app/static /var/www/html/static
ADD files/nginx.conf /etc/nginx/nginx.conf
ADD files/default.conf /etc/nginx/sites-enabled/default

EXPOSE 80

ADD files/entrypoint.sh /opt/app/
CMD ["bash", "-xe", "/opt/app/entrypoint.sh"]
