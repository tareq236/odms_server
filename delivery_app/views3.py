import redis 
import json 
from operator import itemgetter
from itertools import groupby
from collections import defaultdict
from datetime import date as sys_date
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from delivery_app.models import DeliveryInfoModel
from collection_app.utils import update_delivery_info_cache

# Redis connection
redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=redis_pool)

@api_view(['GET'])
def delivery_list(request,sap_id):
    if request.method == 'GET':
        current_date = sys_date.today()
        d_type = request.query_params.get("type")
        date = request.query_params.get("date")
        billing_date = date or current_date
        # Generate Redis key
        cache_key = f"{billing_date}_{sap_id}_delivery-info"
        # Check if data is in cache
        cached_data = r.get(cache_key)
        # Generate update cache key 
        update_cache_key = f"{billing_date}_{sap_id}_update-delivery-info"
        update_cache_data = r.get(update_cache_key)
        if cached_data:
            print("Cache hit")
            json_data = json.loads(cached_data)
            delivery_done_list = []
            delivery_remaining_list = []
            update_cache_data_dict = dict()
            if not update_cache_data:
                update_delivery_info_cache(sap_id)
            update_cache_data= r.get(update_cache_key)
                
            if update_cache_data:
                print("updated_cache_found")
                update_cache_json_data = json.loads(update_cache_data)
                for item in update_cache_json_data:
                    update_cache_dict_key = f'{item["billing_doc_no"]}-{item["matnr"]}-{item["batch"]}'
                    update_cache_data_dict[update_cache_dict_key] = item
            
            for item in json_data:
                item_key = f'{item["billing_doc_no"]}-{item["matnr"]}-{item["batch"]}'
                if item_key in update_cache_data_dict:
                    updated_data = update_cache_data_dict[item_key]
                    item['id'] = updated_data['id']
                    item['list_id'] = updated_data['list_id']
                    item['delivery_status'] = updated_data['delivery_status']
                    item['delivery_quantity'] = updated_data['delivery_quantity']
                    item['delivered_amount'] = updated_data['delivered_amount']
                    item['cash_collection_status'] = updated_data['cash_collection_status']
                    item['cash_collection'] = updated_data['cash_collection']
                    item['return_status'] = updated_data['return_status']
                    item['return_amount'] = updated_data['return_amount']
                    item['delivery_quantity'] = updated_data['delivery_quantity']
                    item['delivery_net_val'] = updated_data['delivery_net_val']
                    item['return_quantity'] = updated_data['return_quantity']
                    item['return_net_val'] = updated_data['return_net_val']
                    delivery_done_list.append(item)
                else:
                    delivery_remaining_list.append(item)
            delivery_list = delivery_done_list + delivery_remaining_list
            if d_type == "Done":
                data_list = delivery_done_list
            elif d_type == "Remaining":
                data_list = delivery_remaining_list
            else:
                data_list = delivery_list
            # print(data_list)   
            # my_data = json.loads(cached_data)
            my_data = data_list 
            # print(my_data)
            if len(data_list) == 0:
                return Response({"success": False, "message": "Data not available!"}, status=status.HTTP_200_OK)
            partner_group = defaultdict(lambda: defaultdict(list))
            for record in my_data:
                partner_group[record['partner']][record['billing_doc_no']].append(record)

            main_data = []

            for partner, billing_group in partner_group.items():
                
                invoice_list = [] 
                
                for billing_doc, records in billing_group.items():
                    billing_date = records[0]['billing_date']
                    route_code = records[0]['route']
                    route_name = records[0]['route_name']
                    da_code = records[0]['da_code']
                    da_name = records[0]['da_name']
                    partner = records[0]['partner']
                    customer_name = records[0]['customer_name']
                    customer_address = records[0]['customer_address']
                    customer_mobile = records[0]['customer_mobile']
                    customer_latitude = records[0]['latitude']
                    customer_longitude = records[0]['longitude']
                    previous_due_amount = records[0]['previous_due_amount'] or 0.0
                    gate_pass_no = records[0]['gate_pass_no']
                    
                    product_list = [] 

                    invoice_data = {
                        'id': records[0]['id'],
                        'billing_doc_no': billing_doc,
                        'billing_date': billing_date,
                        'producer_company': records[0]['producer_company'],
                        'route_code': route_code,
                        'route_name': route_name,
                        'da_code': da_code,
                        'da_name': da_name,
                        'partner': partner,
                        'customer_name': customer_name,
                        'customer_address': customer_address,
                        'customer_mobile': customer_mobile,
                        'customer_latitude': customer_latitude,
                        'customer_longitude': customer_longitude,
                        'latitude': customer_latitude,
                        'longitude': customer_longitude,
                        'previous_due_amount': previous_due_amount,
                        'delivery_status': records[0]['delivery_status'],
                        'gate_pass_no': gate_pass_no,
                        'cash_collection': records[0]['cash_collection'] or 0,
                        'cash_collection_status': records[0]['cash_collection_status'],
                        'vehicle_no': records[0]['vehicle_no'],
                        'transport_type':records[0]['transport_type'],
                        'product_list': product_list,  
                    }
                    invoice_list.append(invoice_data)
                    for record in records:
                        data = {
                            'id': record['list_id'],
                            'matnr': record['matnr'],
                            'quantity': record['quantity'],
                            'tp': record['tp'],
                            'vat': record['vat'],
                            'net_val': record['net_val'],
                            'batch': record['batch'],
                            'material_name': record['material_name'],
                            'brand_description': record['brand_description'],
                            'brand_name': record['brand_name'],
                            'delivery_quantity': record['delivery_quantity'] or 0,
                            'delivery_net_val': record['delivery_net_val'] or 0,
                            'return_quantity': record['return_quantity'] or 0,  # Fixed key
                            'return_net_val': record['return_net_val'] or 0 # Fixed key
                        }
                        product_list.append(data)
                        # print(product_list)
                partner_data = {
                    'billing_date': billing_date,
                    'route_code': route_code,
                    'route_name': route_name,
                    'da_code': da_code,
                    'da_name': da_name,
                    'partner': partner,
                    'customer_name': customer_name,
                    'customer_address': customer_address,
                    'customer_mobile': customer_mobile,
                    'customer_latitude': customer_latitude,
                    'customer_longitude': customer_longitude,
                    'latitude': customer_latitude,
                    'longitude': customer_longitude,
                    'previous_due_amount': previous_due_amount,
                    'gate_pass_no': gate_pass_no,
                    'invoice_list': invoice_list,  # Now properly defined
                }
                main_data.append(partner_data)
            # print(main_data)
            key_func = itemgetter('billing_date', 'partner')
            sorted_data = sorted(main_data, key=key_func)
            return Response({"success": True, "result": sorted_data}, status=status.HTTP_200_OK)
        else:
        
            query = " AND dis.billing_date = CURRENT_DATE() "
            if date != "":
                query = " AND dis.billing_date = '"+date+"' "
            if d_type == 'All':
                query = query + ""
            elif d_type == 'Remaining':
                query = query + "AND d.delivery_status IS NULL"
            else:
                query = query + "AND d.delivery_status = '"+d_type+"'"

            sql = "SELECT dis.*,IFNULL(rs.description, 'No Route Name') AS route_name, " \
                    "sis.billing_type,sis.partner,sis.matnr,sis.quantity,sis.tp,sis.vat,sis.net_val,sis.assigment,sis.gate_pass_no,sis.batch,sis.plant,sis.team,sis.created_on, " \
                    "m.material_name,m.brand_description,m.brand_name,m.producer_company, " \
                    "CONCAT(c.name1,c.name2) customer_name,CONCAT(c.street,c.street1,c.street2) customer_address,c.mobile_no customer_mobile, " \
                    "cl.latitude,cl.longitude,rcl.latitude customer_latitude,rcl.longitude customer_longitude, " \
                    "d.id,dl.id list_id,d.transport_type," \
                    "dl.delivery_quantity,dl.delivery_net_val,dl.return_quantity,dl.return_net_val,IF(d.delivery_status IS NULL,'Pending',d.delivery_status) delivery_status,d.cash_collection,IF(d.cash_collection_status IS NULL,'Pending',d.cash_collection_status) cash_collection_status, (SELECT SUM(d2.due_amount) FROM rdl_delivery d2 WHERE d2.partner=sis.partner AND d2.billing_date<CURRENT_DATE) AS previous_due_amount " \
                    "FROM rdl_delivery_info_sap dis " \
                    "LEFT JOIN rdl_route_sap rs ON dis.route=rs.route " \
                    "INNER JOIN rpl_sales_info_sap sis ON dis.billing_doc_no=sis.billing_doc_no " \
                    "INNER JOIN rpl_material m ON sis.matnr=m.matnr " \
                    "INNER JOIN rpl_customer c ON sis.partner=c.partner " \
                    "LEFT JOIN rdl_customer_location rcl ON c.partner=rcl.customer_id " \
                    "LEFT JOIN (SELECT DISTINCT customer_id, latitude, longitude FROM rdl_customer_location LIMIT 1) cl ON sis.partner = cl.customer_id " \
                    "LEFT JOIN rdl_delivery d ON sis.billing_doc_no=d.billing_doc_no " \
                    "LEFT JOIN rdl_delivery_list dl ON d.id=dl.delivery_id AND sis.matnr=dl.matnr AND sis.batch=dl.batch " \
                    "WHERE dis.da_code = '%s' "+query+" ;"
        
        # print(sql,sap_id)
        data_list = DeliveryInfoModel.objects.raw(sql,[sap_id])
        if len(data_list) == 0:
            return Response({"success": False, "message": "Data not available!"}, status=status.HTTP_200_OK)
        else:
            an_iterator = groupby(data_list, lambda x : x.billing_doc_no)
            data = []
            for key, group in an_iterator:
                key_and_group = {key : list(group)}
                sub_data = []
                for item in key_and_group[key]:
                    rec_qty = 0
                    if item.delivery_quantity is not None:
                        rec_qty = item.delivery_quantity
                    rec_net_val = 0
                    if item.delivery_net_val is not None:
                        rec_net_val = item.delivery_net_val

                    ret_qty = 0
                    if item.return_quantity is not None:
                        ret_qty = item.return_quantity
                    ret_net_val = 0
                    if item.return_net_val is not None:
                        ret_net_val = item.return_net_val

                    sub_data.append({
                        "id": item.list_id,
                        "matnr": item.matnr,
                        "quantity": item.quantity,
                        "tp": item.tp,
                        "vat": item.vat,
                        "net_val": item.net_val,
                        "batch": item.batch,
                        "material_name": item.material_name,
                        "brand_description": item.brand_description,
                        "brand_name": item.brand_name,
                        "delivery_quantity": rec_qty,
                        "delivery_net_val": rec_net_val,
                        "return_quantity": ret_qty,
                        "return_net_val": ret_net_val,
                    })

                    cash_collection = 0
                    if key_and_group[key][0].cash_collection is not None:
                        cash_collection = key_and_group[key][0].cash_collection
                previous_due_amount=key_and_group[key][0].previous_due_amount 
                main_data = {
                    "id": key_and_group[key][0].id,
                    "billing_doc_no": key_and_group[key][0].billing_doc_no,
                    "producer_company": key_and_group[key][0].producer_company,
                    "billing_date": key_and_group[key][0].billing_date,
                    "route_code": key_and_group[key][0].route,
                    "route_name": key_and_group[key][0].route_name,
                    "da_code": key_and_group[key][0].da_code,
                    "da_name": key_and_group[key][0].da_name,
                    "partner": key_and_group[key][0].partner,
                    "customer_name": key_and_group[key][0].customer_name,
                    "customer_address": key_and_group[key][0].customer_address,
                    "customer_mobile": key_and_group[key][0].customer_mobile,
                    "customer_latitude": key_and_group[key][0].customer_latitude,
                    "customer_longitude": key_and_group[key][0].customer_longitude,
                    "previous_due_amount": key_and_group[key][0].previous_due_amount,
                    "latitude": key_and_group[key][0].latitude,
                    "longitude": key_and_group[key][0].longitude,
                    "delivery_status": key_and_group[key][0].delivery_status,
                    "cash_collection": cash_collection,
                    "cash_collection_status": key_and_group[key][0].cash_collection_status,
                    "gate_pass_no": key_and_group[key][0].gate_pass_no,
                    "vehicle_no": key_and_group[key][0].vehicle_no,
                    "transport_type": key_and_group[key][0].transport_type,
                    "product_list": sub_data
                }
                data.append(main_data)
                
                key_func = itemgetter('billing_date', 'partner')
                sorted_data = sorted(data, key=key_func)
                grouped_data = {key: list(group) for key, group in groupby(sorted_data, key=key_func)}
                customer_data = []
                for (billing_date, partner), group in grouped_data.items():
                    customer_data.append({
                        "billing_date": group[0]['billing_date'],
                        "route_code": group[0]['route_code'],
                        "route_name": group[0]['route_name'],
                        "da_code": group[0]['da_code'],
                        "da_name": group[0]['da_name'],
                        "partner": group[0]['partner'],
                        "customer_name": group[0]['customer_name'],
                        "customer_address": group[0]['customer_address'],
                        "customer_mobile": group[0]['customer_mobile'],
                        "customer_latitude": group[0]['customer_latitude'],
                        "customer_longitude": group[0]['customer_longitude'],
                        "previous_due_amount":group[0]['previous_due_amount'],
                        "latitude": group[0]['latitude'],
                        "longitude": group[0]['longitude'],
                        "gate_pass_no": group[0]['gate_pass_no'],
                        "invoice_list": group,
                }) 

            return Response({"success": True, "result": customer_data}, status=status.HTTP_200_OK)