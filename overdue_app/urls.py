from django.urls import path
from .views import overdue_list

urlpatterns = [
    path('list/<int:da_code>',overdue_list,name='overdue_list'),
]
