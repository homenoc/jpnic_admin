from django.urls import path, include

from . import views

app_name = "assignment"
urlpatterns = [
    path("assignment/add", views.add, name="add"),
    path("assignment/change", views.change, name="change"),
    path("assignment/delete", views.delete, name="delete"),
    path("result", views.result, name="result"),
]
