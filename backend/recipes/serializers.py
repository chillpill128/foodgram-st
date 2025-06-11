from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import Recipe, Ingredient, RecipeIngredients


class RecipeSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'

