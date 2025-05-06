from .utils import get_main_data,get_product_return_list,get_due_amount_list,get_product_return_list2, get_da_info
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.db import connection, connections
from datetime import timedelta,datetime
import requests


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
    }
        
    return render_to_pdf("transportation_summary_pdf.html", {
        "transportation": transportation,
        "da_info": da_info,
        "total_transport": total_transport
    }, "transportation_summary.pdf")


def transportation_summary(request, da_code):
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


def transportation_postmortem(request, da_code, date):
    get_transpration_query = """
    SELECT TIME(start_journey_date_time) AS start_time, TIME(end_journey_date_time) AS end_time 
    FROM rdl_conveyance
    WHERE da_code=%s AND DATE(start_journey_date_time)=%s
    ORDER BY start_journey_date_time;
    """
    with connection.cursor() as cursor:
        cursor.execute(get_transpration_query, [da_code, date])
        time_ranges = cursor.fetchall()

    context = {
        'da_code': da_code,
        'date': date,
        'time_ranges': time_ranges,
    }
    return render(request, 'transportation_postmortem.html', context)

from django.http import HttpResponse
from django.db import connection


def view_map_google(request, da_code, date, start_time, end_time):
    query = """
        SELECT latitude, longitude, mv_time
        FROM user_movement
        WHERE user_id = %s AND mv_date = %s AND mv_time BETWEEN %s AND %s
        ORDER BY mv_time
    """
    with connections['postgres'].cursor() as cursor:
        cursor.execute(query, [da_code, date, start_time, end_time])
        rows = cursor.fetchall()

    if not rows:
        return HttpResponse("No data found.")

    points = [
        {'lat': float(r[0]), 'lng': float(r[1]), 'time': str(r[2])}
        for r in rows if r[0] is not None and r[1] is not None
    ]

    context = {
        'da_code': da_code,
        'date': date,
        'start_time': start_time,
        'end_time': end_time,
        'points': points,
        'google_maps_api_key': 'YOUR_API_KEY_HERE',
    }
    return render(request, 'map_google.html', context)


def get_address_from_latlng(lat, lng):
    try:
        url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key=AIzaSyBM8iBM6lt8oSq9Hi4VSTr6r6v2cwhtqp0'
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get('results')
            return results[0]['formatted_address'] if results else "Unknown location"
        return "Unknown location"
    except Exception as e:
        return "Error retrieving location"


def calculate_duration(start, end):
    if not end:
        return "-"
    delta = end - start
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}h {minutes}m {secs}s"


def transportation_postmortem(request, da_code, date):
    query = """
        SELECT 
            start_journey_date_time, end_journey_date_time,
            start_journey_latitude, start_journey_longitude,
            end_journey_latitude, end_journey_longitude,
            transport_mode,transport_cost, journey_status, distance
        FROM rdl_conveyance
        WHERE da_code = %s AND DATE(start_journey_date_time) = %s
        ORDER BY start_journey_date_time;
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [da_code, date])
        rows = cursor.fetchall()

    travel_data = []
    total_distance = 0
    total_duration_seconds = 0
    total_cost = 0

    for row in rows:
        (
            start_dt, end_dt,
            start_lat, start_lng,
            end_lat, end_lng,
            mode, transport_cost, journey_status, distance
        ) = row
        # Time formatting
        start_time = start_dt.strftime("%I:%M:%S %p")
        end_time = end_dt.strftime("%I:%M:%S %p") if end_dt else None
        total_distance += distance or 0
        
        
        query = """
            SELECT latitude, longitude, mv_time
        FROM user_movement
        WHERE user_id = %s AND mv_date = %s AND mv_time BETWEEN %s AND %s
        ORDER BY mv_time
        """
        with connections['postgres'].cursor() as cursor:
            cursor.execute(query, [da_code, date, start_time, end_time])
            res = cursor.fetchall()

        if res:
            start_location = res[0]
            end_location = res[-1]

        # Duration calculation
        duration = calculate_duration(start_dt, end_dt)
        if end_dt:
            total_duration_seconds += int((end_dt - start_dt).total_seconds())
        
        # Get addresses
        from_location = get_address_from_latlng(start_location[0], start_location[1]) if start_location[0] and start_location[1] else "Unknown"
        to_location = get_address_from_latlng(end_location[0], end_location[1]) if end_location[0] and end_location[1] and journey_status == 'end' else "Unknown"

        # Cost
        total_cost += transport_cost or 0

        travel_data.append({
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'from_location': from_location,
            'to_location': to_location,
            'distance': distance,
            'cost': transport_cost,
            'status': journey_status,
            'mode': mode
        })

    # Total duration formatting
    td_hours = total_duration_seconds // 3600
    td_minutes = (total_duration_seconds % 3600) // 60
    td_seconds = total_duration_seconds % 60
    total_duration = f"{td_hours}h {td_minutes}m {td_seconds}s"

    context = {
        'da_code': da_code,
        'date': date,
        'travel_data': travel_data,
        'total_distance': total_distance,
        'total_cost': total_cost,
        'total_duration': total_duration
    }

    return render(request, 'transportation_postmortem.html', context)
