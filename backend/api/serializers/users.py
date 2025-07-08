from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from recipes.models import User, Recipe
from .fields import Base64ImageField


class UserSerializer(DjoserUserSerializer):
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
            return user.subscriptions_author.filter(follower__pk=obj.pk).exists()


class RecipeShortSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']
        read_only_fields = fields


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
        recipes = obj.recipes.order_by('id')
        limit = self.context['request'].query_params.get('recipes_limit', None)
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return RecipeShortSerializer(instance=recipes, many=True,
                                       context=self.context).data


class AvatarUploadSerializer(ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']
