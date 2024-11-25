from django.shortcuts import render
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from collection_app.utils import get_da_route
from collections import defaultdict

# Create your views here.

@api_view(['GET'])
def overdue_list(request,da_code):
    if request.method =='GET':
        route=get_da_route(da_code)
        if not route:
            return Response({"success":True, "message":"Route not found for today"},status=status.HTTP_200_OK)
        
        sql_query = """
        SELECT 
            d.partner, 
            d.billing_doc_no,
            d.billing_date,
            d.gate_pass_no,
            d.da_code,
            d.due_amount,
            d.net_val,
            d.return_amount,
            dl.matnr,
            m.material_name,
            m.producer_company,
            dl.batch,
            dl.delivery_quantity,
            dl.delivery_net_val,
            dl.return_quantity,
            dl.return_net_val,
            CONCAT(c.name1,c.name2) AS customer_name,
            CONCAT(c.street,c.street1,c.street2) AS customer_address,
            c.mobile_no AS customer_mobile,
            ul.full_name AS da_full_name,
            ul.mobile_number AS da_mobile_no
        FROM 
            rdl_delivery d
        LEFT JOIN rpl_customer c ON d.partner=c.partner
        LEFT JOIN rdl_user_list ul ON d.da_code=ul.sap_id
        LEFT JOIN rdl_delivery_list dl ON d.id = dl.delivery_id
        INNER JOIN rpl_material m ON dl.matnr=m.matnr
        WHERE 
            d.route_code = %s 
            AND d.due_amount != 0 
            AND d.billing_date < CURRENT_DATE
        ORDER BY 
            d.partner ASC,  
            d.billing_doc_no ASC;
        """

        # Execute SQL query
        with connection.cursor() as cursor:
            cursor.execute(sql_query, [route])
            rows = cursor.fetchall()
            
        # Group results by partner
        result = defaultdict(lambda: {
            "partner": None,
            "partner_id": None,
            "customer_name": None,
            "customer_address": None,
            "customer_mobile": None,
            "da_full_name": None,
            "da_mobile_no": None,
            "billing_docs": []
        })
        
        for row in rows:
            partner = row[0]
            billing_doc_no = row[1]
            billing_date = row[2].isoformat()  # Convert to string for JSON compatibility      
            # Initialize partner info if not already set
            if result[partner]["partner_id"] is None:
                result[partner]["partner_id"] = partner
                result[partner]["customer_name"] = row[16]  
                result[partner]["customer_address"] = row[17]  
                result[partner]["customer_mobile"] = row[18] 
                 
                result[partner]["da_full_name"] = row[21]  
                result[partner]["da_mobile_no"] = row[22] 

            # Check if the billing_doc_no already exists for this partner
            billing_doc = next((item for item in result[partner]["billing_docs"] if item["billing_doc_no"] == str(billing_doc_no)), None)
            
            if not billing_doc:
                # If billing_doc_no doesn't exist, create a new entry for it
                billing_doc = {
                    "billing_doc_no": str(billing_doc_no),
                    "billing_date": billing_date,
                    "producer_company": row[10],
                    "gate_pass_no": row[3],
                    "da_code": row[4],
                    "due_amount": row[5],
                    "net_val": row[6],
                    "return_amount": row[7],
                    "materials": []
                }
                result[partner]["billing_docs"].append(billing_doc)

            # Append material details to the existing billing_doc's "materials"
            billing_doc["materials"].append({
                "matnr": row[8],
                "material_name": row[9],
                "producer_company": row[10],
                "batch": row[11],
                "delivery_quantity": row[12],
                "delivery_net_val": row[13],
                "return_quantity": row[14],
                "return_net_val": row[15],
            })

        # Convert defaultdict to a regular dict for JSON compatibility
        response_data = list(result.values())
        
        return Response({"success": True, "result": response_data}, status=status.HTTP_200_OK)

