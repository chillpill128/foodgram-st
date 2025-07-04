from django.core.validators import RegexValidator
from djoser.serializers import (
    UserSerializer as djoser_UserSerializer,
    UserCreateSerializer as djoser_UserCreateSerializer
)
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator
from rest_framework import serializers

from recipes.models import User, Recipe
from .fields import Base64ImageField


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
            return user.followers.filter(follower__pk=obj.pk).exists()


# class UserCreateSerializer(djoser_UserCreateSerializer):
#     username = serializers.CharField(max_length=150, required=True,
#                                      validators=[
#                                          RegexValidator(regex=r'^[\w+-.@]+$'),
#                                          UniqueValidator(queryset=User.objects.all())
#                                      ])
#     email = serializers.EmailField(max_length=254, required=True,
#                                    validators=[
#                                        UniqueValidator(queryset=User.objects.all())
#                                    ])
#     first_name = serializers.CharField(max_length=150, required=True)
#     last_name = serializers.CharField(max_length=150, required=True)
#     password = serializers.CharField(max_length=128, write_only=True)
#
#     class Meta:
#         model = User
#         fields = ['email', 'id', 'username', 'first_name', 'last_name', 'password']
#         read_only_fields = ['id']



class RecipeShortSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class UserWithRecipesSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar']
        read_only_fields = fields

    def get_recipes_count(self, obj):
        # Получает кол-во рецептов из аннотации (в случае списка пользователей)
        if hasattr(obj, 'recipes_count'):
            return obj.recipes_count
        else:
            # Или вычисляет на лету (для единичного пользователя).
            return obj.recipes.count()

    def get_recipes(self, obj):
        # В случае параметра из урла берём ограниченное кол-во рецептов
        if hasattr(obj, 'recipes_limited'):
            recipes = obj.recipes_limited
        else:
            # Если параметра нет, фильтровать ничего не нужно, выберем все записи.
            recipes = obj.recipes.all()
        return RecipeShortSerializer(instance=recipes, many=True,
                                       context=self.context).data


class AvatarUploadSerializer(ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']
