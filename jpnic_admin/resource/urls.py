from django.urls import path, include

from . import views

app_name = "resource"
urlpatterns = [
    path("", views.ip_address, name="index"),
    path("resource/", views.resource, name="resource"),
]
