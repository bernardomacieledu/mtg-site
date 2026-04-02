from django.urls import path, include

urlpatterns = [
    path('api/', include('mtg_api.urls')),
    path('api/auth/', include('auth_app.urls')),
]
