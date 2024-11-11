from django.urls import path
from .views import ReturnReasonView


urlpatterns = [
    path('return_reason', ReturnReasonView.as_view(),name='return_reason'),
]