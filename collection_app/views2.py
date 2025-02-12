import decimal
from operator import itemgetter
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from itertools import groupby
import pytz
from delivery_app.models import DeliveryInfoModel, DeliveryModel,DeliveryListModel
from delivery_app.serializers import DeliverySerializer
from datetime import datetime,timedelta, date
from django.db import connection
from django.utils import timezone
from .models import PaymentHistory, ReturnListModel
from decimal import Decimal
from . import utils
from .constants import tz_Dhaka

import redis
import json
from datetime import date as sys_date
from collections import defaultdict

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

@api_view(['PUT'])
def cash_collection_save(request, pk):
    try:
        delivery = DeliveryModel.objects.get(pk=pk)
    except DeliveryModel.DoesNotExist:
        return Response({"error": "Delivery not found"}, status=status.HTTP_404_NOT_FOUND)

    tz_Dhaka = pytz.timezone('Asia/Dhaka')
    serializer = DeliverySerializer(delivery, data=request.data, partial=True)
    if serializer.is_valid():
        sql = "SELECT sis.matnr,sis.batch,sis.vat,sis.quantity,sis.net_val,sis.tp FROM rpl_sales_info_sap sis WHERE sis.billing_doc_no = %s;"
        billing_doc_no = request.data.get('billing_doc_no')
        results = execute_raw_query(sql,[billing_doc_no])
        data=dict()
        total_net_val=0.00
        
        """ For Cashing"""
        billing_date=request.data.get('billing_date')
        da_code=request.data.get('da_code')
        cache_key = f'{billing_date}_{da_code}_delivery-info'
        update_keys = dict()
        
        for result in results:
            matnr,batch,vat,quantity,net_val=result[0],result[1],float(result[2]),float(result[3]),float(result[4])
            total_net_val = total_net_val + vat + net_val
            unit_vat,unit_price= vat/quantity, net_val/quantity
            unit_total = unit_vat + unit_price
            key=str(str(matnr)+str(batch))
            data[key]={
                "matnr":matnr,
                "batch":batch,
                "vat":vat,
                "quantity":quantity,
                "net_val":net_val,
                "unit_vat":unit_vat,
                "unit_price":unit_price,
                "unit_total":unit_total
            }
            
        serializer.validated_data['net_val']=total_net_val
        
        if request.data.get('type') == "cash_collection":
            cash_collection = request.data.get('cash_collection')
            delivery_items=request.data.get('deliverys',[])
            return_amount=0.00
            
            for items in delivery_items:
                matnr=str(items['id'])
                batch=items['batch']
                return_quantity=float(items["return_quantity"])
                key=str(str(matnr)+str(batch))
                amount=data[key]["unit_total"]*return_quantity
                # amount=(data[matnr]['unit_vat']+data[matnr]['unit_price'])*items['return_quantity']
                if return_quantity>data[key]['quantity']:
                    return Response({"success":False,"message":"Return quantity exceeds total quantity"},status=status.HTTP_200_OK)
                return_amount+=amount
                unit_total = data[key]['unit_total']
                new_quantity = 0
                if return_quantity>0:
                    try:
                        record=DeliveryListModel.objects.get(delivery=pk,matnr=matnr,batch=batch)
                        # calculate new return quantity
                        old_quantity=float(record.return_quantity)
                        new_quantity=return_quantity-old_quantity
                        # update record
                        record.return_quantity=return_quantity
                        record.return_net_val = data[key]["unit_total"]*return_quantity
                        record.delivery_quantity-=Decimal(new_quantity)
                        record.delivery_net_val-=Decimal(data[key]["unit_total"]*new_quantity)
                        record.save()
                        
                        # print(new_quantity)
                        if new_quantity>0:
                            utils.CreateReturnList(
                                matnr=matnr,
                                batch=batch,
                                return_quantity=new_quantity,
                                return_net_val=data[key]["unit_total"]*new_quantity,
                                billing_doc_no=billing_doc_no,
                                billing_date=request.data.get('billing_date'),
                                da_code=request.data.get('da_code'),
                                gate_pass_no=request.data.get('gate_pass_no'),
                                partner=request.data.get('partner'),
                                route_code=request.data.get('route_code'),
                                return_time=ReturnListModel.ReturnTime.v1
                            )
                           
                    except DeliveryListModel.DoesNotExist:
                        return Response({"success":False,"message":"matnr does not found"},status=status.HTTP_200_OK)
                    
                update_key = f'{billing_doc_no}{matnr}{batch}'
                update_keys[update_key] = {
                    "return_quantity": return_quantity,
                    "new_return_quantity": new_quantity,
                    "return_net_val": data[key]["unit_total"]*return_quantity,
                    "cash_collection":cash_collection,
                    "unit_total":unit_total,
                    "new_return_net_val": float(unit_total * new_quantity)
                }
                    
                    
                    

            if return_amount>0.00:
                serializer.validated_data['return_status']=1
            serializer.validated_data['return_amount']=return_amount
            due = total_net_val - float(cash_collection)-return_amount
            serializer.validated_data['due_amount']=round(due, 2);
            serializer.validated_data['cash_collection_date_time'] = datetime.now(tz_Dhaka)
            # Create Payment History Object
            utils.CreatePaymentHistoryObject(
                billing_doc_no = billing_doc_no,
                partner = delivery.partner,
                da_code = delivery.da_code,
                route_code = delivery.route_code,
                cash_collection = cash_collection,
                cash_collection_date_time = datetime.now(tz_Dhaka),
                cash_collection_latitude = request.data.get('cash_collection_latitude', None),cash_collection_longitude = request.data.get('cash_collection_latitude', None)
                )

            cache_data = r.get(cache_key)
            if cache_data:
                data_list = json.loads(cache_data)
                for data in data_list:
                    key = f'{data["billing_doc_no"]}{data["matnr"]}{data["batch"]}'
                    
                    if key in update_keys:
                        data["cash_collection_status"] = "Done"
                        data["return_quantity"] = update_keys[key]["return_quantity"]
                        data["return_net_val"] = update_keys[key]["return_net_val"]
                        data["cash_collection"] = update_keys[key]["cash_collection"]
                        data["delivery_quantity"] -= update_keys[key]["new_return_quantity"]
                        data["delivery_net_val"] -= update_keys[key]["new_return_net_val"]
                        data["return_amount"] += update_keys[key]["return_net_val"]
                        if update_keys[key]["return_quantity"]:
                            data["return_status"] = 1
                        print("update keys found .......................")
                        print('key is',key)
                            
                json_data = json.dumps(data_list, default=custom_serializer)
                r.set(cache_key, json_data, ex=36000)
                # print("cache updated")
                # print(json_data)
        
        elif request.data.get('type') == "return":
            serializer.validated_data['return_date_time'] = datetime.now(tz_Dhaka)
            
        serializer.update(delivery, serializer.validated_data)
        
        return Response({"success": True, "result": serializer.data}, status=status.HTTP_200_OK)
    # print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

