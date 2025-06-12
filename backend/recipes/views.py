from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


from .models import Recipe, Ingredient
from .serializers import (
    RecipeViewSerializer,
    RecipeChangeSerializer,
    IngredientSerializer
)


class RecipesViewSet(ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        'recipeingredients',
        'recipeingredients__ingredient'
    )
    serializer_class = RecipeViewSerializer

    def get_serializer_class(self):
        if self.action in ('create', 'update'):
            return RecipeChangeSerializer
        return RecipeViewSerializer

    @action(methods=['get'], detail=False, permission_classes=[],
            url_path='download_shopping_cart', url_name='download-shopping-cart')
    def download_shopping_cart(self, request):
        """Скачать список покупок в csv-формате"""
        return Response()

    @action(methods=['post'], detail=True, permission_classes=[],
            url_path='shopping_cart', url_name='add-shopping-cart')
    def add_shopping_cart(self, request, pk=None):
        """Добавить рецепт в список покупок"""
        return Response()

    @action(methods=['delete'], detail=True, permission_classes=[],
            url_path='shopping_cart', url_name='delete-shopping-cart')
    def delete_shopping_cart(self, request, pk=None):
        """Удалить рецепт из списка покупок"""
        return Response()

    @action(methods=['post'], detail=True, permission_classes=[],
            url_path='favorite', url_name='add-favorite')
    def add_to_favorite(self, request, pk=None):
        """Добавить рецепт в избранное"""
        return Response()

    @action(methods=['delete'], detail=True, permission_classes=[],
            url_path='favorite', url_name='delete-favorite')
    def delete_from_favorite(self, request, pk=None):
        """Удалить рецепт из избранного"""
        return Response()


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

