import datetime
import pytz
import redis
import json
from django.db import connection
from .models import PaymentHistory,ReturnListModel
from delivery_app.models import DeliveryInfoModel
from decimal import Decimal
from datetime import date as sys_date

# Redis connection
redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=redis_pool)


def get_da_route(da_code):
    sql="SELECT billing_doc_no,route FROM rdl_delivery_info_sap WHERE da_code='%s' AND billing_date=CURRENT_DATE LIMIT 1"
    data=DeliveryInfoModel.objects.raw(sql,[da_code])
    data_list=list(data)
    if data_list:
        route = data_list[0].route
        return route
    return None

def CreatePaymentHistoryObject(billing_doc_no,partner,da_code,route_code,cash_collection,cash_collection_date_time,cash_collection_latitude,cash_collection_longitude):
    PaymentHistory.objects.create(
        billing_doc_no=billing_doc_no,
        partner=partner, 
        da_code=da_code,
        route_code=route_code,
        cash_collection=cash_collection,
        cash_collection_date_time=cash_collection_date_time,
        cash_collection_latitude=cash_collection_latitude,
        cash_collection_longitude=cash_collection_longitude
    )
    
def CreateReturnList(matnr, batch, return_quantity, return_net_val, billing_doc_no, billing_date, da_code, gate_pass_no, partner, route_code,return_time):
    ReturnListModel.objects.create(
        matnr=matnr,
        batch=batch,
        return_quantity=return_quantity,
        return_net_val=return_net_val,
        return_time=return_time,
        billing_doc_no=billing_doc_no,
        billing_date=billing_date,
        da_code=da_code,
        gate_pass_no=gate_pass_no,
        partner=partner,
        route_code=route_code
    )
    
def update_delivery_info_cache(sap_id):
    query = """
        SELECT 
            d.id, 
            d.billing_doc_no, 
            d.billing_date, 
            d.da_code, 
            d.delivery_status, 
            IF(d.cash_collection_status IS NULL, 'Pending', d.cash_collection_status) AS cash_collection_status, 
            d.return_status, 
            d.net_val AS delivered_amount, 
            d.cash_collection, 
            d.return_amount, 
            d.due_amount,
            dl.id AS list_id,
            dl.matnr,
            dl.batch,
            dl.quantity,
            dl.net_val ,
            dl.vat,
            dl.delivery_quantity,
            dl.delivery_net_val,
            dl.return_quantity,
            dl.return_net_val
        FROM rdl_delivery d 
        INNER JOIN rdl_delivery_list dl ON d.id = dl.delivery_id
        WHERE billing_date = CURRENT_DATE AND da_code = %s;
    """
    print('sap id is: ',sap_id)
    with connection.cursor() as cursor:
        cursor.execute(query, [sap_id]) 
        results = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description] 

    data_dict = [dict(zip(column_names, row)) for row in results]
    def custom_serializer(obj):
        if isinstance(obj, sys_date):
            return obj.isoformat()  # Convert date to string (YYYY-MM-DD format)
        if isinstance(obj, Decimal):
            return float(obj)
        return obj

    json_data=json.dumps(data_dict,default=custom_serializer)
    update_cache_key = f"{sys_date.today()}_{sap_id}_update-delivery-info"
    r.set(update_cache_key, json_data)