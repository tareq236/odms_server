from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from report_app.models import ReportOneModel
from django.db import connection
from collection_app.utils import get_da_route
import redis
import json 
from datetime import date as sys_date
from decimal import Decimal

# Redis connection
redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=redis_pool)

def execute_raw_query(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()
    return results

def execute_raw_query_v1(sql, params):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    
@api_view(['GET'])
def activity_for_map(request,sap_id,date):
    if request.method == 'GET':
        sql = "SELECT * FROM rdl_delivery WHERE da_code = %s AND created_at LIKE %s;"
        params = [sap_id, f"{date}%"]
        result = execute_raw_query_v1(sql, params)
        return Response({"success": True, "result": result}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def dashboard_report(request,sap_id):
    if request.method == 'GET':
        route=get_da_route(sap_id)
        # if not route:
        #     return Response({"success": True, "message": "No route found for today"}, status=status.HTTP_200_OK)
        sql= "SELECT " \
	            "(SELECT COUNT(DISTINCT dis.billing_doc_no) c FROM rdl_delivery_info_sap dis WHERE dis.billing_date = CURRENT_DATE() AND dis.da_code = '%s' AND dis.route = %s ) total_delivary," \
	            "(SELECT COUNT(*) c FROM rdl_delivery d WHERE d.billing_date = CURRENT_DATE() AND d.da_code = '%s' AND d.route_code = %s ) total_delivary_done, " \
	            "(SELECT COUNT(*) c FROM rdl_delivery d WHERE d.billing_date = CURRENT_DATE() AND d.da_code = '%s' AND d.route_code = %s AND delivery_status = 'Done' AND cash_collection_status IS NULL) total_collection, " \
                "(SELECT COUNT(*) c FROM rdl_delivery d WHERE d.billing_date = CURRENT_DATE() AND d.da_code = '%s' AND d.route_code = %s AND cash_collection_status = 'Done') total_collection_done, " \
                "(SELECT SUM(sis.net_val + sis.vat ) c FROM rdl_delivery_info_sap dis INNER JOIN rpl_sales_info_sap sis ON dis.billing_doc_no=sis.billing_doc_no WHERE dis.billing_date = CURRENT_DATE() AND dis.da_code = '%s' AND dis.route = %s) total_gate_pass_amount," \
	            "(SELECT SUM(d.cash_collection) c FROM rdl_delivery d WHERE d.billing_date = CURRENT_DATE() AND d.da_code = '%s' AND d.route_code = %s AND delivery_status = 'Done' AND cash_collection_status = 'Done') total_collection_amount," \
	            "(SELECT SUM(dl.return_net_val) c FROM rdl_delivery d INNER JOIN rdl_delivery_list dl ON d.id=dl.delivery_id WHERE d.billing_date = CURRENT_DATE() AND d.da_code = '%s' AND d.route_code = %s AND d.delivery_status = 'Done' AND dl.return_net_val IS NOT NULL) total_return_amount," \
	            "(SELECT SUM(rl.return_quantity) c FROM rdl_return_list rl WHERE rl.billing_date = CURRENT_DATE() AND rl.da_code = '%s' AND rl.route_code = %s ) total_return_quantity," \
                "(SELECT SUM(d.due_amount) c FROM rdl_delivery d WHERE d.billing_date = CURRENT_DATE() AND d.da_code = '%s' AND d.route_code = %s) total_due;"     
        result = execute_raw_query(sql,[sap_id,route,sap_id,route,sap_id,route,sap_id,route,sap_id,route,sap_id,route,sap_id,route,sap_id,route,sap_id,route])
        
        time_interval=1*60*1000 #millisecond
        distance=10 #meter

        return Response({"success": True, "result": [{
            'delivery_remaining': result[0][0]-result[0][1],
            'delivery_done': result[0][1],
            'cash_remaining': result[0][2],
            'cash_done': result[0][3],
            'sap_id': sap_id,
            'total_gate_pass_amount': result[0][4],
            'total_collection_amount': result[0][5], 
            'total_return_amount': result[0][6], 
            'total_return_quantity': result[0][7],
            'due_amount_total': result[0][8],
            'previous_day_due': 0,
            'time_interval': time_interval,
            'distance': distance
        }]}, status=status.HTTP_200_OK)
        
@api_view(['GET'])
def dashboard_report_v2(request, sap_id):
    if request.method == 'GET':
        time_interval=1*60*1000 #millisecond
        distance=10 #meter
        
        cache_key = f"{sys_date.today()}_{sap_id}_delivery-info"
        cached_data = r.get(cache_key)
        update_cache_key = f"{sys_date.today()}_{sap_id}_update-delivery-info"
        update_cache_data = r.get(update_cache_key)
        
        if cached_data:
            remaining_set= set()
            delivered_set= set()
            cash_collection_set= set()
            return_set = set()
            data_dict = json.loads(cached_data.decode('utf-8'))
            # for item in data_dict:
            #     billing_doc_no = item['billing_doc_no']
            #     if item["delivery_status"] == "Done":
            #         delivered_set.add(billing_doc_no)    
            #     if item["delivery_status"] == "Pending":
            #         remaining_set.add(billing_doc_no)
            #     if item["cash_collection_status"] == "Done":
            #         cash_collection_set.add(billing_doc_no)
            #     if item["return_status"] == 1:
            #         return_set.add(billing_doc_no)
            total = set()
            done = set()
            collection = set()
            return_ = set()
            for item in data_dict:
                total.add(item['billing_doc_no'])
                
            if update_cache_data:
                update_cache_json_data = json.loads(update_cache_data.decode('utf-8'))
                for item in update_cache_json_data:
                    done.add(item['billing_doc_no'])
                    if item["cash_collection_status"] == "Done":
                        collection.add(item['billing_doc_no'])
                    if item["return_status"] == 1:
                        return_.add(item['billing_doc_no'])
            else:
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
                r.set(update_cache_key, json_data)
                
                for data in data_dict:
                    done.add(data['billing_doc_no'])
                    if data["cash_collection_status"] == "Done":
                        collection.add(data['billing_doc_no'])
                    if data["return_status"] == 1:
                        return_.add(data['billing_doc_no'])
                print("cache data updated successfully")
                                            
            data = [{
                'delivery_remaining': len(total)-len(done),
                'delivery_done': len(done),
                'cash_remaining': len(done) - len(collection),
                'cash_done': len(collection),
                'sap_id': sap_id,
                # 'total_gate_pass_amount': result[0][4],
                # 'total_collection_amount': result[0][5], 
                # 'total_return_amount': result[0][6], 
                'total_return_quantity':  len(return_),
                # 'due_amount_total': result[0][8],
                # 'previous_day_due': 0,
                'time_interval': time_interval,
                'distance': distance
            }]
            
            return Response({"success": True, "result": data}, status=status.HTTP_200_OK)
        else:
            query_1 ="""
                SELECT COUNT(DISTINCT dis.billing_doc_no)
                FROM rdl_delivery_info_sap dis 
                INNER JOIN rpl_sales_info_sap sis ON dis.billing_doc_no = sis.billing_doc_no
                INNER JOIN rpl_customer c ON sis.partner = c.partner
                WHERE dis.billing_date = CURRENT_DATE AND dis.da_code=%s;
            """
            total_delivery_result = execute_raw_query(query_1,[sap_id])
            total_delivery = total_delivery_result[0][0] if total_delivery_result else 0
            
            query_2 = """
                SELECT d.billing_doc_no, d.delivery_status, d.cash_collection_status, d.return_status
                FROM rdl_delivery d 
                WHERE d.billing_date = CURRENT_DATE AND d.da_code = %s;
            """
            delivery_list = execute_raw_query(query_2,[sap_id])
            delivery_done = 0
            delivery_remaining = 0
            cash_collection =0
            cash_collection_remaining = 0
            return_invoice = 0
            
            for result in delivery_list:
                if result[1] == 'Done':
                    delivery_done += 1
                if result[2] == 'Done':
                    cash_collection += 1
                if result[3] == 1:
                    return_invoice += 1
                    
            delivery_remaining = total_delivery - delivery_done
            cash_collection_remaining = delivery_done - cash_collection
            
            data = [{
                'delivery_remaining': delivery_remaining,
                'delivery_done': delivery_done,
                'cash_remaining': cash_collection_remaining,
                'cash_done': cash_collection,
                'sap_id': sap_id,
                # 'total_gate_pass_amount': result[0][4],
                # 'total_collection_amount': result[0][5], 
                # 'total_return_amount': result[0][6], 
                'total_return_quantity': return_invoice,
                # 'due_amount_total': result[0][8],
                # 'previous_day_due': 0,
                'time_interval': time_interval,
                'distance': distance
            }]
            
            return Response({"success": True, "result": data}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def dashboard_info(request,sap_id):
    if request.method == 'GET':   
        sap_query="""
            SELECT COUNT(DISTINCT sis.gate_pass_no) total_gate_pass,SUM(sis.net_val+ sis.vat) total_gate_pass_amount,COUNT(DISTINCT sis.partner) total_customer, GROUP_CONCAT(DISTINCT dis.route ORDER BY dis.route ASC SEPARATOR ', ') AS routes, GROUP_CONCAT(DISTINCT r.route_name ORDER BY dis.route ASC SEPARATOR ' || ') AS route_name 
            FROM rdl_delivery_info_sap dis 
            INNER JOIN rpl_sales_info_sap sis ON dis.billing_doc_no=sis.billing_doc_no 
            INNER JOIN rpl_customer c ON sis.partner=c.partner
            LEFT JOIN rdl_route_wise_depot r ON dis.route = r.route_code
            WHERE dis.da_code=%s AND dis.billing_date=CURRENT_DATE;
        """
        result=execute_raw_query(sap_query,[sap_id])
        route_id=None
        route_name=""
        total_gate_pass=0
        total_gate_pass_amount=0
        total_customer=0
        if result:
            total_gate_pass=result[0][0]
            total_gate_pass_amount=result[0][1]
            total_customer=result[0][2]
            route_id=result[0][3]
            route_name=result[0][4]
        
        response_data={
            'route_id': route_id,
            'route_name': route_name,
            'total_gate_pass':total_gate_pass,
            'total_gate_pass_amount':total_gate_pass_amount,
            'total_customer':total_customer
        }
        return Response({"success":True,"result":response_data},status=status.HTTP_200_OK)
    
@api_view(['GET'])
def dashboard_info_v2(request, sap_id):
    if request.method == 'GET':
        sql="""
        SELECT dis.route, dr.route_name, dr.depot_code, dr.depot_name, 
        COUNT(DISTINCT sis.gate_pass_no) total_gate_pass, 
        SUM(sis.net_val + sis.vat) total_gate_pass_amount, 
        COUNT(DISTINCT sis.partner) total_customer
        FROM rdl_delivery_info_sap dis
        INNER JOIN rpl_sales_info_sap sis ON dis.billing_doc_no = sis.billing_doc_no
        LEFT JOIN rdl_route_wise_depot dr ON dis.route = dr.route_code
        WHERE dis.da_code = %s AND dis.billing_date = CURRENT_DATE
        GROUP BY dis.route, dr.route_name, dr.depot_code, dr.depot_name;
        """
        results=execute_raw_query(sql,[sap_id])
        total_gate_pass=0
        total_gate_pass_amount=0.0
        total_customer=0
        for result in results:
            total_gate_pass+=result[4]
            total_gate_pass_amount+=float(result[5])
            total_customer+=result[6]
        routes=[]
        for result in results:
            route_code = result[0]
            route={
                "route": result[0],
                "route_name": result[1],
                # "depot_code": result[2],
                # "depot_name": result[3],
                # "total_gate_pass": result[4],
                # "total_gate_pass_amount": result[5],
            }
            routes.append(route)
        data={
            'total_gate_pass': total_gate_pass,
            'total_gate_pass_amount': total_gate_pass_amount,
            'total_customer': total_customer,
            'routes': routes
        }
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)
    return Response({"success":False, "message":"Method not allowed"}, status=status.HTTP_400_BAD_REQUEST)