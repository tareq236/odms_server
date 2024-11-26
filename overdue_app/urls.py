from django.urls import path
from .views import overdue_list,collect_overdue

urlpatterns = [
    path('list/<int:da_code>',overdue_list,name='overdue_list'),
    path('collect',collect_overdue,name='collect_overdue'),
]
