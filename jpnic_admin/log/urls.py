from django.urls import path, include

from . import views

app_name = "log"
urlpatterns = [
    path("", views.index, name="index"),
]
