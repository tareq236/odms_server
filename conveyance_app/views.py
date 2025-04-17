from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ConveyanceModel, TransportModeModel
from .serializers import ConveyanceSerializer, TransportModeSerializer, DaMovementInfoSerializer
from django.utils import timezone
from django.db.models import Q
from django.db import connections
import pytz

class TransportModeListView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve distinct transport_mode values from the database
        transport_modes = TransportModeModel.objects.filter(
            Q(status=1)
        )
        serializer = TransportModeSerializer(transport_modes, many=True)
        return Response({"success": True, "result": serializer.data}, status=status.HTTP_200_OK)
    
# Conveyance List (Today or filter by date)
class ConveyanceListView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the 'date' and 'da_code' from the query parameters
        date_filter = request.GET.get('date', timezone.now().date())
        da_code = request.GET.get('da_code')
        
        # Ensure da_code is provided, if not, return an error response
        if not da_code:
            return Response({"success": False, "message": "da_code is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Filter conveyances by date and da_code
        conveyances = ConveyanceModel.objects.filter(
            Q(start_journey_date_time__date=date_filter) & Q(da_code=da_code)
        )
        
        # Serialize the result
        serializer = ConveyanceSerializer(conveyances, many=True)
        
        return Response({"success": True, "result": serializer.data}, status=status.HTTP_200_OK)

# Start Journey
class StartJourneyView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        data['journey_status'] = 'live'
        data['start_journey_date_time'] = timezone.now()  # Auto set current time for start
        serializer = ConveyanceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "result": serializer.data}, status=status.HTTP_200_OK)
        return Response({"success": False, "message": serializer.errors}, status=status.HTTP_200_OK)
    

# End Journey
class EndJourneyView(APIView):
    def put(self, request, id, *args, **kwargs):
        try:
            conveyance = ConveyanceModel.objects.get(id=id)
        except ConveyanceModel.DoesNotExist:
            return Response({"success": False, "message": "Journey not found"}, status=status.HTTP_200_OK)
        
        dhaka_tz = pytz.timezone('Asia/Dhaka')
        user_id = conveyance.da_code
        mv_date = conveyance.start_journey_date_time.date()
        start_time = conveyance.start_journey_date_time.time().strftime('%H:%M:%S')
        end_time = timezone.now().astimezone(dhaka_tz).time().strftime('%H:%M:%S')
        
        with connections['postgres'].cursor() as cursor:
            cursor.execute("""
                WITH MovementData AS (
                    SELECT 
                        user_id,
                        mv_date,
                        geo_location,
                        mv_time,
                        LEAD(geo_location) OVER (PARTITION BY user_id, mv_date ORDER BY mv_time) AS next_geo_location,
                        LEAD(mv_time) OVER (PARTITION BY user_id, mv_date ORDER BY mv_time) AS next_mv_time
                    FROM user_movement
                    WHERE user_id = %s 
                        AND mv_date = %s 
                        AND mv_time >= %s  
                        AND mv_time <= %s
                ),
                Distances AS (
                    SELECT 
                        user_id,
                        mv_date,
                        mv_time,
                        next_mv_time,
                        ST_Distance(geo_location, next_geo_location) AS distance,
                        EXTRACT(EPOCH FROM (next_mv_time - mv_time)) / 60 AS duration_minutes
                    FROM MovementData
                    WHERE next_geo_location IS NOT NULL AND next_mv_time IS NOT NULL
                )
                SELECT 
                    user_id,
                    mv_date,
                    SUM(distance) / 1000 AS total_distance_km,
                    SUM(duration_minutes) AS total_time_minutes
                FROM Distances
                GROUP BY user_id, mv_date;
            """, [str(user_id), str(mv_date), str(start_time), str(end_time)])

            result = cursor.fetchone()
        total_distance_km = result[2] if result else 0
        total_time_minutes = result[3] if result else 0

        end_time = timezone.now().astimezone(dhaka_tz)
        data = request.data
        conveyance.end_journey_latitude = data.get('end_journey_latitude')
        conveyance.end_journey_longitude = data.get('end_journey_longitude')
        conveyance.end_journey_date_time = timezone.now()  # Auto set current time for end
        conveyance.transport_mode = data.get('transport_mode')
        conveyance.transport_cost = data.get('transport_cost')
        conveyance.journey_status = 'end'
        conveyance.time_duration = total_time_minutes
        conveyance.distance = total_distance_km
        conveyance.save()

        serializer = ConveyanceSerializer(conveyance)
        return Response({"success": True, "result": serializer.data}, status=status.HTTP_200_OK)
    
    
class DaMovementInfoView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = DaMovementInfoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "result": serializer.data}, status=status.HTTP_200_OK)
        return Response({"success": False, "message": serializer.errors}, status=status.HTTP_200_OK)
