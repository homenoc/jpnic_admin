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
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('add_assignment/', views.add_assignment, name='add_assignment'),
    path('change_assignment/', views.change_assignment, name='change_assignment'),
    path('return_assignment/', views.return_assignment, name='return_assignment'),
    path('result', views.result, name='result'),
    path('add_person/', views.add_person, name='add_person'),
    path('change_person/', views.change_person, name='change_person'),
    path('add_as/', views.add_as, name='add_as'),
    path('list_as/', views.list_as, name='list_as'),
    path('ca', views.ca, name='ca'),
    path('test/', views.get_jpnic_info, name='get_jpnic_info'),
    path('__debug__/', include('debug_toolbar.urls')),
    # path('event_viewer/', views.event_viewer, name='event_viewer'),
]
