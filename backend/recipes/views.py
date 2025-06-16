import csv
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q, IntegerField
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from common.permissions import IsAuthorOrCreateAndReadOnly
from .models import FavoriteRecipe, Ingredient, Recipe, ShoppingCart
from .filters import RecipeFilterSet
from .serializers import (
    IngredientSerializer,
    RecipeViewSerializer,
    RecipeChangeSerializer,
    RecipeShortLinkSerializer,
)
from .serializers_short import RecipeShortenSerializer


User = get_user_model()


class RecipesViewSet(ModelViewSet):
    """Рецепты"""
    queryset = Recipe.objects.all().prefetch_related(
        'recipeingredients',
        'recipeingredients__ingredient'
    )
    serializer_class = RecipeViewSerializer
    filterset_class = RecipeFilterSet
    permission_classes = [AllowAny, IsAuthorOrCreateAndReadOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Count(
                                   'favorite__id',
                                   filter=Q(favorite__user=user),
                                   output_field=IntegerField()
                ),
                is_in_shopping_cart=Count('shopping_cart__id',
                                          filter=Q(shopping_cart__user=user),
                                          output_field=IntegerField()
              ))
            # print(queryset.query)
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeChangeSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipe = serializer.save()
        recipe.is_favorited = 1 if recipe.favorite.count() > 0 else 0
        recipe.is_in_shopping_cart = 1 if recipe.shopping_cart.count() > 0 else 0

        headers = self.get_success_headers(serializer.data)
        serializer_resp = RecipeViewSerializer(
            instance=recipe,
            context=self.get_serializer_context()
        )
        return Response(serializer_resp.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        recipe = serializer.save()
        if getattr(recipe, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        recipe.is_favorited = 1 if recipe.favorite.count() > 0 else 0
        recipe.is_in_shopping_cart = 1 if recipe.shopping_cart.count() > 0 else 0
        serializer_resp = RecipeViewSerializer(
            instance=recipe,
            context=self.get_serializer_context()
        )
        return Response(serializer_resp.data)

    @action(methods=['GET'], detail=False, permission_classes=[AllowAny],
            url_path='download_shopping_cart', url_name='download-shopping-cart')
    def download_shopping_cart(self, request):
        """Скачать список покупок в csv-формате"""

        user = request.user if request.user.is_authenticated else User.objects.first()

        ingredients = (Ingredient.objects.filter(
            recipeingredients__recipe__shopping_cart__user=user
        ).order_by('name').distinct().annotate(
            amount=Sum('recipeingredients__amount'))
        )

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

    @action(methods=['GET'], detail=True,
            permission_classes=[AllowAny],
            url_path='get-link', url_name='get-short-link')
    def get_link(self, request, pk=None):
        """Получить короткую ссылку"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': _('Страница не найдена')},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(RecipeShortLinkSerializer(
            instance=recipe,
            context=self.get_serializer_context()
        ).data)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated],
            url_path='shopping_cart', url_name='add-delete-shopping-cart')
    def add_delete_shopping_cart(self, request, pk=None):
        """Добавить или удалить рецепт из списка покупок"""

        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': _('Страница не найдена')},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user

        if request.method == 'POST':
            return self._add_to_shopping_cart(recipe, user)
        elif request.method == 'DELETE':
            return self._delete_from_shopping_cart(recipe, user)
        else:
            return Response({'detail': 'Метод не поддерживается'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def _add_to_shopping_cart(self, recipe, user):
        if ShoppingCart.objects.filter(user=user, recipe=recipe).count() != 0:
            return Response({'detail': 'Рецепт уже в списке покупок'},
                            status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
        return Response(
            RecipeShortenSerializer(instance=recipe,
                                    context=self.get_serializer_context()
                                    ).data,
            status=status.HTTP_201_CREATED
        )

    def _delete_from_shopping_cart(self, recipe, user):
        """Удалить рецепт из списка покупок"""
        try:
            recipe_in_shopping_cart = ShoppingCart.objects.get(
                user=user, recipe=recipe)
        except ShoppingCart.DoesNotExist:
            return Response({'detail': _('Рецепт не добавлен в список покупок')},
                            status=status.HTTP_400_BAD_REQUEST)

        recipe_in_shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated],
            url_path='favorite', url_name='add-favorite')
    def add_delete_favorite(self, request, pk=None):
        """Добавить рецепт в избранное"""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': _('Рецепт не найден')},
                            status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if request.method == 'POST':
            return self._add_to_favorite(recipe, user)
        elif request.method == 'DELETE':
            return self._delete_from_favorite(recipe, user)
        else:
            return Response({'detail': 'Метод не поддерживается'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def _add_to_favorite(self, recipe, user):
        if FavoriteRecipe.objects.filter(user=user, recipe=recipe).count() != 0:
            return Response({'detail': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST)
        FavoriteRecipe.objects.create(user=user, recipe=recipe)
        return Response(
            RecipeShortenSerializer(instance=recipe,
                                    context=self.get_serializer_context()
                                    ).data,
            status=status.HTTP_201_CREATED
        )

    def _delete_from_favorite(self, recipe, user):
        """Удалить рецепт из избранного"""
        try:
            recipe_favorite = FavoriteRecipe.objects.get(
                user=user, recipe=recipe)
        except FavoriteRecipe.DoesNotExist:
            return Response({'detail': 'Рецепт ещё не добавлен в избранное'},
                            status=status.HTTP_400_BAD_REQUEST)

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
    filterset_fields = ['name']
    pagination_class = None
