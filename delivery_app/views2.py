from operator import itemgetter
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from delivery_app.models import DeliveryInfoModel
from delivery_app.serializers import DeliverySerializer
from itertools import groupby
from datetime import date, datetime
import pytz
from collection_app.utils import CreateReturnList
from collection_app.models import ReturnListModel
from .models import DeliveryModel
import redis 
import json
import decimal
from django.db import connection

# Redis connection
redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=redis_pool)

def custom_serializer(obj):
    if isinstance(obj, date):
        return obj.isoformat()  # Convert date to string (YYYY-MM-DD format)
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    return obj

def execute_raw_query(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()
    return results

@api_view(['POST'])
def delivery_save(request):
    if request.method == 'POST':
        tz_Dhaka = pytz.timezone('Asia/Dhaka')
        productList = []
        # print("data requested", request.data)
        net_val=0.0
        total_return_amount=0.0
        billing_date = request.data['billing_date']
        da_code = request.data ['da_code']
        cache_key = f'{billing_date}_{da_code}_delivery-info'
        cached_data = r.get(cache_key)

            
        # print(serializer.errors)
        update_keys = dict()
        billing_doc_no = request.data['billing_doc_no']
        query_billing_doc_no = billing_doc_no
        delivery_latitude = request.data['delivery_latitude']
        delivery_longitude = request.data['delivery_longitude']
        
        
        for item in request.data['deliverys']:
            unit_vat=item["vat"]/item["quantity"]
            unit_price=item["net_val"]/item["quantity"]
            unit_price_with_vat=unit_vat+unit_price
            return_amount=round(unit_price_with_vat*item["return_quantity"],2)
            delivery_amount=round(unit_price_with_vat * item["delivery_quantity"],2)
            quantity=item["quantity"]
            net_val=round(net_val+round(unit_price_with_vat*quantity,2),2)
            total_return_amount=round(total_return_amount+return_amount,2)
            # print("test....",net_val, total_return_amount)
            
            # generate update keys
            key=f'{billing_doc_no}{item['matnr']}{item['batch']}'
            update_keys[key] = {
                "delivery_latitude":delivery_latitude,
                "delivery_longitude":delivery_longitude,
                "delivery_quantity":item['delivery_quantity'],
                "delivery_net_val":delivery_amount,
                "return_quantity":item['return_quantity'],
                "return_net_val":return_amount,
                "delivery_status": "Done",
            }
            
            
            productList.append({
                "batch": item["batch"],
                "tp": item["tp"],
                "vat": item["vat"],
                "net_val": round(item["net_val"],2),
                "matnr": item["matnr"],
                "quantity": item["quantity"],
                
                "delivery_quantity": item["delivery_quantity"],
                "return_quantity": item["return_quantity"],
                "delivery_net_val": delivery_amount,
                "return_net_val": return_amount,
                
            })
            
            
            if item["return_quantity"]:
                CreateReturnList(
                    matnr = item["matnr"],
                    batch = item["batch"],
                    return_quantity = item["return_quantity"],
                    return_net_val = return_amount,
                    return_time=ReturnListModel.ReturnTime.v0,
                    billing_doc_no = request.data['billing_doc_no'],
                    billing_date = request.data['billing_date'],
                    da_code = request.data['da_code'],
                    gate_pass_no = request.data['gate_pass_no'],
                    partner = request.data['partner'],
                    route_code = request.data['route_code']
                )
            else:
                continue
                # print('no return quantity')
        # return Response({"success": True,"message":"success"},status=status.HTTP_200_OK)
        return_status=DeliveryModel.ReturnStatus.v0
        if total_return_amount>0.0:
            return_status=DeliveryModel.ReturnStatus.v1
        total_due_amount=round(net_val-total_return_amount,2)
        # print("testing.......",total_due_amount,net_val)
        main_data = {
            "billing_date": request.data['billing_date'],
            "billing_doc_no": request.data['billing_doc_no'],
            "cash_collection": request.data['cash_collection'],
            "da_code": request.data['da_code'],
            "delivery_latitude": request.data['delivery_latitude'],
            "delivery_longitude": request.data['delivery_longitude'],
            "delivery_status": request.data['delivery_status'],
            "gate_pass_no": request.data['gate_pass_no'],
            "last_status": request.data['last_status'],
            "partner": request.data['partner'],
            "route_code": request.data['route_code'],
            "transport_type": request.data['transport_type'],
            "type": request.data['type'],
            "vehicle_no": request.data['vehicle_no'],
            "net_val":net_val,
            "due_amount":total_due_amount,
            "return_amount":total_return_amount,
            "return_status":return_status,
            "deliverys": productList,
        }

        serializer = DeliverySerializer(data=main_data, partial=True)
        if serializer.is_valid():
            if request.data.get('type') == "delivery":
                serializer.validated_data['delivery_date_time'] = datetime.now(tz_Dhaka)
            if request.data.get('type') == "cash_collection":
                serializer.validated_data['cash_collection_date_time'] = datetime.now(tz_Dhaka)
            if request.data.get('type') == "return":
                serializer.validated_data['return_date_time'] = datetime.now(tz_Dhaka)
            instance = serializer.save()
            print(instance.id)
            delivery_item_ids = list(instance.deliverys.values_list('id', flat=True))
            print(delivery_item_ids)
            print(f"================== Data Saved ===============")
            
            saved_delivery_id = instance.id
            saved_list_id = dict()
            for item in instance.deliverys.all():
                key = f"{item.matnr}{item.batch}"
                saved_list_id[key] = item.id
            
            print("=================================")
            print(saved_delivery_id)
            print(saved_list_id)
            print("=============================")
            if cached_data:
                print('cache hit')
                data_list = json.loads(cached_data)
                # print(f"Executing query with billing_doc_no: {query_billing_doc_no}")

                # sql ="""
                #     SELECT d.id, dl.id as list_id
                #     FROM rdl_delivery d 
                #     INNER JOIN rdl_delivery_list dl ON d.id = dl.delivery_id
                #     where d.billing_doc_no = %s;
                # """
                # results=execute_raw_query(sql, [query_billing_doc_no])
                # delivery_id = results[0][0]
                # delivery_list_id = results[0][1]
                for data in data_list:
                    key = f'{data["billing_doc_no"]}{data["matnr"]}{data["batch"]}'
                    billing_doc_no = data["billing_doc_no"]
                    list_key = f'{data['matnr']}{data['batch']}'
                    if key in update_keys:
                        print(list_key)
                        data["id"] = saved_delivery_id
                        data["list_id"] = saved_list_id[list_key]
                        data["delivery_status"] = "Done"
                        data["delivery_quantity"] = update_keys[key]["delivery_quantity"]
                        data["delivery_net_val"] = update_keys[key]["delivery_net_val"]
                        data["return_quantity"] = update_keys[key]["return_quantity"]
                        data["return_net_val"] = update_keys[key]["return_net_val"]
                        if data["return_amount"]:
                            data["return_amount"] += update_keys[key]["return_net_val"]
                        else:
                            data["return_amount"] = update_keys[key]["return_net_val"]
                        if update_keys[key]["return_quantity"]:
                            data["return_status"] =1
                # r.set(data_list)
                json_data=json.dumps(data_list,default=custom_serializer)
                r.set(cache_key,json_data, ex=36000) #  10 hour timeout
            return Response({"success": True, "result":'sucess'}, status=status.HTTP_200_OK)

        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            