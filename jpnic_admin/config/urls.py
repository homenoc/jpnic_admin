from django.urls import path, include

from . import views

app_name = "config"
urlpatterns = [
    path("as/", views.list_as, name="list_as"),
    path("as/add", views.add_as, name="add_as"),
    path("notice/", views.notice, name="notice"),
]
