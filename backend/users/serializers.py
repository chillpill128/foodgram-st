from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework import serializers

from .models import User


class UserViewSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar']


class UserAddSerializer(ModelSerializer):
    password = serializers.CharField(max_length=128, write_only=True)
    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name', 'password']
        read_only_fields = ['id']


class PasswordChangeSerializer(Serializer):
    new_password = serializers.CharField(max_length=128)
    current_password = serializers.CharField(max_length=128)


class GetTokenSerializer(Serializer):
    password = serializers.CharField(max_length=128)
    email = serializers.EmailField()

