from django.urls import path
from .views import upload_apk, app_info

# Url Patterns
urlpatterns = [
    path('upload',upload_apk, name='upload_apk'),
    path('info',app_info, name='app_info'),
]
