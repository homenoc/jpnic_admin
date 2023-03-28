"""jpnic_admin URL Configuration

The `urlpatterns` result routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from jpnic_admin import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("resource/", views.resource, name="resource"),
    path("log/", include("jpnic_admin.log.urls")),
    path("config/", include("jpnic_admin.config.urls")),
    path("assignment/", include("jpnic_admin.assignment.urls")),
    path("person/", include("jpnic_admin.person.urls")),
    path("search/", views.search, name="search"),
    path("add_assignment1/", views.add_assignment1, name="add_assignment"),
    path("test/", views.get_jpnic_info, name="get_jpnic_info"),
    path("__debug__/", include("debug_toolbar.urls")),
]
