from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('src.apps.core.urls')),
    path('api/auth/', include('src.apps.auth.urls')),
    path('api/chat/', include('src.apps.chatbot.urls')),
    path('api/admin/', include('src.apps.admin.urls')),
    path('api/reports/', include('src.apps.reports.urls')),
    path('api/analytics/', include('src.apps.analytics.urls')),
]
