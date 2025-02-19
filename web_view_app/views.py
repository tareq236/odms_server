from .utils import get_main_data,get_product_return_list,get_due_amount_list,get_product_return_list2, get_da_info
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.db import connection
from datetime import timedelta,datetime

def reports(request,da_code):
    return render(request, "reports.html",{"da_code":da_code})

def summary(request, da_code):
    data_list=get_main_data(da_code)
    data = data_list[0]
    da_info = data_list[1]
    total=data_list[2]
    return render(request, "summary.html", {"data": data,"da_info":da_info,"total":total,"status":"view"})


def render_to_pdf(template_src, context_dict,file_name):
    template = render_to_string(template_src, context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    
    # Create PDF from HTML
    pisa_status = pisa.CreatePDF(template, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + template + '</pre>')
    return response

def da_summary_pdf(request,da_code):
    data_list=get_main_data(da_code)
    data = data_list[0]
    da_info = data_list[1]
    total=data_list[2]
    return render_to_pdf('summary.html', {'data': data,"da_info":da_info,"total":total,"status":"print"},"delivery_summary.pdf")

def test(request,da_code):
    # data=get_main_data(da_code)
    da_info={
        "da_code":da_code
    }
    return render(request,"test.html",{"da_info":da_info,"status":"view"})

def product_return_list_v2(request,da_code):
    data_list=get_product_return_list2(da_code)
    return_list=data_list[0]
    total_return=data_list[1]
    da_info={
        "da_code":da_code
    }
    return render(request,"return_list_v2.html",{"return_list":return_list,"total_return":total_return,"da_info":da_info,"status":"view"})

def due_amount_list(request,da_code):
    data_list=get_due_amount_list(da_code)
    da_info={
        "da_code":da_code,
    }
    return render(request,"due_amount_list.html",{"data":data_list,"da_info":da_info})

def product_return_list_v1(request,da_code):
    data_list=get_product_return_list(da_code)
    da_info={
        "da_code":da_code
    }
    return render(request,"return_list_v1.html",{"data":data_list,"da_info":da_info})


def admin_dashboard_manual(request):
    return render(request, "admin_dashboard_manual.html")

def dashboard_manual(request):
    return render(request, "dashboard_manual.html")


def transportation_summary_pdf(request, da_code):
    query = """
    SELECT 
        cv.start_journey_date_time,
        cv.end_journey_date_time,
        cv.transport_cost,
        cv.transport_mode
    FROM rdl_conveyance cv
    WHERE cv.da_code = %s 
        AND DATE(cv.start_journey_date_time) = CURRENT_DATE  
        AND cv.journey_status = 'end';
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [da_code])
        results = cursor.fetchall()
    
    transportation = []
    total_cost = 0.00 
    total_duration = timedelta() 
    
    for result in results:
        start_datetime = result[0]  
        end_datetime = result[1]   
        transport_cost = float(result[2])
        transport_mode = result[3]
        
        # Extract only time
        start_time = start_datetime.strftime("%I:%M:%S %p")  # 12-hour format
        end_time = end_datetime.strftime("%I:%M:%S %p") 
        
        # Calculate duration
        time_diff = end_datetime - start_datetime
        hours, remainder = divmod(time_diff.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours:
            duration = f"{int(hours)} hour {int(minutes)} min {int(seconds)} sec"
        elif minutes:
            duration = f"{int(minutes)} min {int(seconds)} sec"
        else:
            duration = f"{int(seconds)} sec"
            
        total_cost += transport_cost
        total_duration += time_diff

        transportation.append({
            "start_time": start_time, 
            "end_time": end_time,
            "duration": duration,
            "cost": transport_cost,
            "genre": transport_mode.split('"')[1]
        })
    
    # Format total duration properly
    total_hours, remainder = divmod(total_duration.total_seconds(), 3600)
    total_minutes, total_seconds = divmod(remainder, 60)
    
        
    if total_hours:
        total_duration_str = f"2{int(total_hours)} hour 2{int(total_minutes)} min 2{int(total_seconds)} sec"
    elif total_minutes:
        total_duration_str = f"{int(total_minutes)} min {int(total_seconds)} sec"
    else:
        total_duration_str = f"{int(total_seconds)} sec"
    
    da = get_da_info(da_code)
    da_info = {
        "da_code": da_code,
        "da_name": da[0][0],
        "billing_date": da[0][1]
    }
    
    total_transport = {
        "total_duration": total_duration_str,
        "total_cost": total_cost,
    }
        
    return render_to_pdf("transportation_summary_pdf.html", {
        "transportation": transportation,
        "da_info": da_info,
        "total_transport": total_transport
    }, "transportation_summary.pdf")


def transportation_summary2(request, da_code):
    query = """
    SELECT 
        cv.start_journey_date_time,
        cv.end_journey_date_time,
        cv.transport_cost,
        cv.transport_mode
    FROM rdl_conveyance cv
    WHERE cv.da_code = %s 
        AND DATE(cv.start_journey_date_time) = CURRENT_DATE    
        AND cv.journey_status = 'end';
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [da_code])
        results = cursor.fetchall()
    
    transportation = []
    total_cost = 0.00 
    total_duration = timedelta() 
    
    for result in results:
        start_datetime = result[0]  
        end_datetime = result[1]   
        transport_cost = float(result[2])
        transport_mode = result[3]
        
        # Format time with AM/PM and include seconds
        start_time = start_datetime.strftime("%I:%M:%S %p")
        end_time = end_datetime.strftime("%I:%M:%S %p")  

        # Calculate duration
        time_diff = end_datetime - start_datetime
        hours, remainder = divmod(time_diff.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours:
            duration = f"{int(hours)} hour {int(minutes)} min {int(seconds)} sec"
        elif minutes:
            duration = f"{int(minutes)} min {int(seconds)} sec"
        else:
            duration = f"{int(seconds)} sec"

        total_cost += transport_cost
        total_duration += time_diff

        transportation.append({
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "hours": int(hours),
            "minutes": int(minutes),
            "seconds": int(seconds),
            "cost": transport_cost,
            "genre": transport_mode.split('"')[1] if '"' in transport_mode else transport_mode
        })
    
    # Format total duration properly
    total_hours, remainder = divmod(total_duration.total_seconds(), 3600)
    total_minutes, total_seconds = divmod(remainder, 60)
    
    if total_hours:
        total_duration_str = f"{int(total_hours)} hour {int(total_minutes)} min {int(total_seconds)} sec"
    elif total_minutes:
        total_duration_str = f"{int(total_minutes)} min {int(total_seconds)} sec"
    else:
        total_duration_str = f"{int(total_seconds)} sec"
    
    da = get_da_info(da_code)
    da_info = {
        "da_code": da_code,
        "da_name": da[0][0],
        "billing_date": da[0][1]
    }
    
    total_transport = {
        "total_duration": total_duration_str,
        "total_cost": total_cost,
        "total_hours": int(total_hours),
        "total_minutes": int(total_minutes),
        "total_seconds": int(total_seconds)
    }
        
    return render(request, "transportation_summary.html", {
        "transportation": transportation,
        "da_info": da_info,
        "total_transport": total_transport
    })
