from rest_framework import serializers
from .models import ConveyanceModel,TransportModeModel, DaMovementInfo

class ConveyanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConveyanceModel
        fields = '__all__'

class TransportModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportModeModel
        fields = '__all__'
        
class DaMovementInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DaMovementInfo
        fields = '__all__'