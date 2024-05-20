from django.urls import path, include

from . import views

app_name = "info"
urlpatterns = [
    path("", views.ip_address, name="index"),
    path("resource/", views.resource, name="resource"),
    path("resource/export/", views.export_resources, name="export_resources"),
]
