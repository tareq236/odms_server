from django.urls import path
from .views import upload_apk

# Url Patterns
urlpatterns = [
    path('upload',upload_apk, name='upload_apk')
]
