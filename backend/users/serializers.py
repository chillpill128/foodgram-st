from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework import serializers

from .models import User
from recipes.utils import Base64ImageField
from recipes.serializers_short import RecipeShortenSerializer


class UserViewSerializer(ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar']

    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None

class UserAddSerializer(ModelSerializer):
    password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'password']
        read_only_fields = ['id']


class UserWithRecipesSerializer(ModelSerializer):
    recipes = RecipeShortenSerializer(many=True)
    recipes_count = serializers.IntegerField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar']

    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None



class PasswordChangeSerializer(Serializer):
    new_password = serializers.CharField(max_length=128)
    current_password = serializers.CharField(max_length=128)


class GetTokenSerializer(Serializer):
    password = serializers.CharField(max_length=128)
    email = serializers.EmailField()


class AvatarUploadSerializer(ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']


class AvatarViewSerializer(ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['avatar']

    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None
