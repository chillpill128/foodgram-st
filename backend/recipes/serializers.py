import base64
from django.core.files.base import ContentFile
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import Recipe, Ingredient, RecipeIngredients
from users.serializers import UserViewSerializer


class RecipeIngredientSerializer(ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeViewSerializer(ModelSerializer):
    author = UserViewSerializer()
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True, read_only=True
    )
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields =  ['id', 'author', 'ingredients', 'is_favorited',
                   'is_in_shopping_cart', 'name', 'image', 'text',
                   'cooking_time']

    def get_image(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None


class RecipeChangeSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'



