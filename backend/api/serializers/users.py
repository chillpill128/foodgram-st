from django.core.validators import RegexValidator
from djoser.serializers import (
    UserSerializer as djoser_UserSerializer,
    UserCreateSerializer as djoser_UserCreateSerializer
)
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator
from rest_framework import serializers

from recipes.models import User
from .fields import Base64ImageField
from .shorten import RecipeShortenSerializer


class UserSerializer(djoser_UserSerializer):
    avatar = serializers.ImageField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
              'last_name', 'is_subscribed', 'avatar']
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        elif hasattr(obj, 'is_subscribed'):
            return bool(obj.is_subscribed)
        else:
            return user.followers.filter(pk=obj.pk).exists()


class UserCreateSerializer(djoser_UserCreateSerializer):
    username = serializers.CharField(max_length=150, required=True,
                                     validators=[
                                         RegexValidator(regex=r'^[\w+-.@]+$'),
                                         UniqueValidator(queryset=User.objects.all())
                                     ])
    email = serializers.EmailField(max_length=254, required=True,
                                   validators=[
                                       UniqueValidator(queryset=User.objects.all())
                                   ])
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name', 'password']
        read_only_fields = ['id']


class UserWithRecipesSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar']
        read_only_fields = fields

    def get_recipes_count(self, obj):
        if hasattr(obj, 'recipes_count'):
            return obj.recipes_count
        else:
            return obj.recipes.count()

    def get_recipes(self, obj):
        if hasattr(obj, 'recipes_limited'):
            recipes = obj.recipes_limited
        else:
            recipes = obj.recipes.all()
        return RecipeShortenSerializer(instance=recipes, many=True,
                                       context=self.context).data


class AvatarUploadSerializer(ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']


class AvatarViewSerializer(ModelSerializer):
    avatar = serializers.ImageField()

    class Meta:
        model = User
        fields = ['avatar']
        read_only_fields = fields


# Не отлавливает момент, когда в поле avatar передана пустая картинка
# class AvatarSerializer(ModelSerializer):
#     avatar = serializers.SerializerMethodField()
#
#     class Meta:
#         model = User
#         fields = ['avatar']
#         extra_kwargs = {
#             'avatar': {
#                 'write_only': True,
#                 'required': True,
#             }
#         }
#
#     def get_avatar(self, obj):
#         if obj.avatar:
#             return self.context['request'].build_absolute_uri(obj.avatar.url)
#         return None
#
#     def to_internal_value(self, data):
#         internal_value = super().to_internal_value(data)
#         internal_value['avatar'] = Base64ImageField(required=True) \
#                                     .to_internal_value(data.get('avatar'))
#         return internal_value
