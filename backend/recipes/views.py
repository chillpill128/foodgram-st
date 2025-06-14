from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import FavoriteRecipe, Ingredient, Recipe, ShoppingCart
from .serializers import (
    RecipeViewSerializer,
    RecipeChangeSerializer,
    RecipeShortenSerializer,
    IngredientSerializer,
)


class RecipesViewSet(ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        'recipeingredients',
        'recipeingredients__ingredient'
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = RecipeViewSerializer

    def get_serializer_class(self):
        if self.action in ('create', 'update'):
            return RecipeChangeSerializer
        return self.serializer_class

    @action(methods=['get'], detail=False, permission_classes=[],
            url_path='download_shopping_cart', url_name='download-shopping-cart')
    def download_shopping_cart(self, request):
        """Скачать список покупок в csv-формате"""
        return Response()


    @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated],
            url_path='shopping_cart', url_name='add-shopping-cart')
    def add_shopping_cart(self, request, pk=None):
        """Добавить рецепт в список покупок"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Страница не найдена'},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user

        ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
        return Response(
            RecipeShortenSerializer(instance=recipe),
            status=status.HTTP_201_CREATED
        )

    @action(methods=['delete'], detail=True, permission_classes=[IsAuthenticated],
            url_path='shopping_cart', url_name='delete-shopping-cart')
    def delete_shopping_cart(self, request, pk=None):
        """Удалить рецепт из списка покупок"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Страница не найдена'},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user

        try:
            recipe_in_shopping_cart = ShoppingCart.objects.get(
                user=user, recipe=recipe)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Страница не найдена'},
                            status=status.HTTP_404_NOT_FOUND)

        recipe_in_shopping_cart.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated],
            url_path='favorite', url_name='add-favorite')
    def add_to_favorite(self, request, pk=None):
        """Добавить рецепт в избранное"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Страница не найдена'},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user

        FavoriteRecipe.objects.get_or_create(user=user, recipe=recipe)
        return Response(
            RecipeShortenSerializer(instance=recipe),
            status=status.HTTP_201_CREATED
        )

    @action(methods=['delete'], detail=True, permission_classes=[IsAuthenticated],
            url_path='favorite', url_name='delete-favorite')
    def delete_from_favorite(self, request, pk=None):
        """Удалить рецепт из избранного"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Страница не найдена'},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user

        try:
            recipe_favorite = ShoppingCart.objects.get(
                user=user, recipe=recipe)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Страница не найдена'},
                            status=status.HTTP_404_NOT_FOUND)

        recipe_favorite.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
