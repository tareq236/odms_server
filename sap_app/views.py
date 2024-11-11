from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .constants import ReturnReason
from .serializers import ReturnReasonSerializer

# Create your views here.
class ReturnReasonView(APIView):
    def get(self,request):
        return_reasons= [{'code': choice.value, 'reason': choice.label} for choice in ReturnReason]
        serializer = ReturnReasonSerializer(return_reasons, many=True)
        return Response(serializer.data)