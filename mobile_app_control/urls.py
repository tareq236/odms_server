from django.urls import path
from .views import upload_apk, app_info, app_error_info, update_app_error

# Url Patterns
urlpatterns = [
    path('upload',upload_apk, name='upload_apk'),
    path('info',app_info, name='app_info'),
    path('error_info', app_error_info, name='app_error_info'),
    path('update_error_info',update_app_error),
]
