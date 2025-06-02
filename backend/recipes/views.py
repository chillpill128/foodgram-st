from rest_framework.viewsets import ModelViewSet
from rest_framework import generics
from .models import Recipe, Ingredient
from .serializers import RecipeSerializer, IngredientSerializer


class RecipesViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


