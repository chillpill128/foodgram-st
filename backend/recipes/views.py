import csv
from django.http import HttpResponse
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import FavoriteRecipe, Ingredient, Recipe, ShoppingCart
from users.models import User
from .serializers import (
    IngredientSerializer,
    RecipeViewSerializer,
    RecipeChangeSerializer,
    RecipeShortenSerializer,
    RecipeShortLinkSerializer,
)


class RecipesViewSet(ModelViewSet):
    """Рецепты"""
    queryset = Recipe.objects.all().prefetch_related(
        'recipeingredients',
        'recipeingredients__ingredient'
    )
    serializer_class = RecipeViewSerializer
    filterset_fields = ['author__id', 'is_subscribed', 'is_in_shopping_cart', 'is_favorited']
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('create', 'update'):
            return RecipeChangeSerializer
        return self.serializer_class

    @action(methods=['get'], detail=False, permission_classes=[AllowAny],
            url_path='download_shopping_cart', url_name='download-shopping-cart')
    def download_shopping_cart(self, request):
        """Скачать список покупок в csv-формате"""

        user = request.user if request.user.is_authenticated else User.objects.first()

        ingredients = (Ingredient.objects.filter(
            recipeingredients__recipe__shopping_cart__user=user
        ).order_by('name').distinct().annotate(
            amount=Sum('recipeingredients__amount'))
        )
        # print(ingredients.query)

        response = HttpResponse(
            content_type = 'text/csv',
            headers = {
                'Content-Disposition': 'attachment; filename="Покупки.csv"',
                'Cache-Control': 'no-cache',
            })

        writer = csv.writer(response)
        writer.writerow(['№', _('Название'), _('Количество'), _('Единица измерения')])
        for n, ing in enumerate(ingredients):
            writer.writerow([n, ing.name, ing.amount, ing.measurement_unit])
        return response

    @action(methods=['get'], detail=True, permission_classes=[],
            url_path='get_link', url_name='get-short-link')
    def get_link(self, request, pk=None):
        """Получить короткую ссылку"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': _('Страница не найдена')},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(RecipeShortLinkSerializer(instance=recipe).data)

    @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated],
            url_path='shopping_cart', url_name='add-shopping-cart')
    def add_shopping_cart(self, request, pk=None):
        """Добавить рецепт в список покупок"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': _('Страница не найдена')},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user

        ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
        return Response(
            RecipeShortenSerializer(instance=recipe).data,
            status=status.HTTP_201_CREATED
        )

    @action(methods=['delete'], detail=True, permission_classes=[IsAuthenticated],
            url_path='shopping_cart', url_name='delete-shopping-cart')
    def delete_shopping_cart(self, request, pk=None):
        """Удалить рецепт из списка покупок"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': _('Страница не найдена')},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user

        try:
            recipe_in_shopping_cart = ShoppingCart.objects.get(
                user=user, recipe=recipe)
        except Recipe.DoesNotExist:
            return Response({'detail': _('Страница не найдена')},
                            status=status.HTTP_404_NOT_FOUND)

        recipe_in_shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated],
            url_path='favorite', url_name='add-favorite')
    def add_to_favorite(self, request, pk=None):
        """Добавить рецепт в избранное"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': _('Страница не найдена')},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user

        FavoriteRecipe.objects.get_or_create(user=user, recipe=recipe)
        return Response(
            RecipeShortenSerializer(instance=recipe).data,
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
    """Ингридиенты"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    search_fields = ['^name']
