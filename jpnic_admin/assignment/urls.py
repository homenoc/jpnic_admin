from django.urls import path, include

from . import views

app_name = "assignment"
urlpatterns = [
    path("add", views.add, name="add"),
    path("change", views.change, name="change"),
    path("delete", views.delete, name="delete"),
    path("result", views.result, name="result"),
]
