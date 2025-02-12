from django.urls import path
from delivery_app import views,views2
from . views3 import delivery_list

urlpatterns = [
    path('list/<int:sap_id>', views.delivery_list),
    # path('v2/list/<int:sap_id>', views.delivery_list_v2),
    path('v2/list/<int:sap_id>', delivery_list),
    path('save', views2.delivery_save),
]