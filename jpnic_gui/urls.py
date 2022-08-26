"""jpnic_gui URL Configuration

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

from jpnic_gui import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('add_assignment/', views.add_assignment, name='add_assignment'),
    # path('add_assignment/verify', views.verify_add_assignment, name='verify_add_assignment'),
    path('add_person/', views.add_person, name='add_person'),
    path('test/', views.get_jpnic_info, name='get_jpnic_info'),
    path('__debug__/', include('debug_toolbar.urls')),
    # path('event_viewer/', views.event_viewer, name='event_viewer'),
]
