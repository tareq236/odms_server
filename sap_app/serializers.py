from rest_framework import serializers

class ReturnReasonSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    reason = serializers.CharField()