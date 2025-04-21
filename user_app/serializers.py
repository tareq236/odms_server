from rest_framework import serializers
from .models import UsersList,AdminUserList

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersList
        exclude = ('password',)

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersList
        fields = ['sap_id', 'full_name', 'mobile_number','user_type','password']

class AdminUserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUserList
        exclude = ('password',)
