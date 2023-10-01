"""
URL configuration for ccache project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from rest_framework.authtoken import views as authtoken_views
from account import views as account_views
from cachemanager import views as cacheman_views


urlpatterns = [
    path('storage/<filename>/', cacheman_views.get_saved_file, name="get_file"),
    path('storage/', cacheman_views.Storage.as_view()),
    path('account/', account_views.AccountManager.as_view()),
    path('register/', account_views.register),
    path("api-token-auth/", authtoken_views.obtain_auth_token),
    path('api-auth/', include('rest_framework.urls')),
    path('admin/', admin.site.urls),
]
