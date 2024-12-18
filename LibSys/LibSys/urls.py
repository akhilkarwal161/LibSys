
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('Home.urls')),
    path('users/', include('django.contrib.auth.urls')),
    path("debug/", include("debug_toolbar.urls")),

]
