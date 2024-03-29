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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from jpnic_admin import views
from jpnic_admin.resource import views as resource

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", resource.ip_address, name="index"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("info/", include("jpnic_admin.resource.urls")),
    path("log/", include("jpnic_admin.log.urls")),
    path("config/", include("jpnic_admin.config.urls")),
    path("assignment/", include("jpnic_admin.assignment.urls")),
    path("person/", include("jpnic_admin.person.urls")),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
