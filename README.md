# JPNIC Admin

[![Publish Docker image(prod)](https://github.com/homenoc/jpnic_admin/actions/workflows/build-prod.yaml/badge.svg)](https://github.com/homenoc/jpnic_admin/actions/workflows/build-prod.yaml)
[![Publish Docker image(dev)](https://github.com/homenoc/jpnic_admin/actions/workflows/build-dev.yaml/badge.svg)](https://github.com/homenoc/jpnic_admin/actions/workflows/build-dev.yaml)

## デプロイ(Docker)方法
`/docker`フォルダにサンプルファイルとREADMEをご覧ください。

### Memo

```
pipenv run python3 manage.py migrate
pipenv run python3 manage.py createdomain
pipenv run python3 manage.py createsuperuser
```

### build for lima

```
DJANGO_SETTINGS_MODULE=jpnic_admin.production_settings
echo ${DJANGO_SETTINGS_MODULE}
sudo docker-compose build
sudo docker-compose up
```