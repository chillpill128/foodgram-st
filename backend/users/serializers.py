from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework import serializers

from .models import User


class UserListSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar']


class UserAddSerializer(ModelSerializer):
    password = serializers.CharField()
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password']


class UserAddResponseSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name']


class PasswordChangeSerializer(Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()


class GetTokenSerializer(Serializer):
    password = serializers.CharField()
    email = serializers.EmailField()

