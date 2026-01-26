from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('src.apps.core.urls')),
    path('api/auth/', include('src.apps.auth.urls')),
    path('api/users/', include('src.apps.core.users_urls')),
    path('api/blockchain/', include('src.apps.blockchain.urls')),
]
