"""
URL configuration for TaskFlow project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from projects.views import profile, signup, custom_logout, google_callback



urlpatterns = [
    path('', lambda request: redirect('projects:project_list')),
    path('admin/', admin.site.urls),
    path('projects/', include('projects.urls', namespace='projects')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/signup/', signup, name = 'signup'),
    path('accounts/logout/', custom_logout, name='logout'),
    path('accounts/google-callback/', google_callback, name='google_callback'),
]

