from rest_framework.viewsets import ModelViewSet
from .models import Recipe, Ingredient
from .serializers import RecipeSerializer, IngredientSerializer


class RecipesViewSet(ModelViewSet):
    model = Recipe
    serializer_class = RecipeSerializer


class IngredientViewSet(ModelViewSet):
    model = Ingredient
    serializer_class = IngredientSerializer


