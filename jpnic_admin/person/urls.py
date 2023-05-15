from django.urls import path, include

from . import views

app_name = "person"
urlpatterns = [
    path("add", views.add, name="add"),
    path("change", views.change, name="change"),
]
