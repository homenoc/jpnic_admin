# JPNIC GUI

```
pipenv run python3 manage.py migrate
pipenv run python3 manage.py createdomain
pipenv run python3 manage.py createsuperuser
```

### build for lima

```
DJANGO_SETTINGS_MODULE=jpnic_gui.production_settings
echo ${DJANGO_SETTINGS_MODULE}
sudo docker-compose build
sudo docker-compose up
```