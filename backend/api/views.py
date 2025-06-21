import csv
import os
from django.http import HttpResponse, FileResponse
from django.db.models import  Count, IntegerField, Q, OuterRef,Prefetch, Sum, Subquery
from djoser.views import UserViewSet as djoser_UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import (
    IsAuthorOrCreateAndReadOnly, IsUserSelfOrCreateAndReadOnly
)
from recipes.models import FavoriteRecipe, Ingredient, Recipe, ShoppingCart
from users.models import User, Subscription
from .filters import RecipeFilterSet
from .serializers.recipes import (
    IngredientSerializer,
    RecipeViewSerializer,
    RecipeChangeSerializer,
    RecipeShortLinkSerializer,
)
from .serializers.users import (
    UserViewSerializer,
    UserAddSerializer,
    UserWithRecipesSerializer,
    PasswordChangeSerializer,
    AvatarUploadSerializer,
    AvatarViewSerializer,
)
from .serializers.shorten import RecipeShortenSerializer


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

        response = FileResponse(filename='Покупки.txt')

        response = HttpResponse(
            content_type = 'text/csv',
            headers = {
                'Content-Disposition': 'attachment; filename="Покупки.csv"',
                'Cache-Control': 'no-cache',
            })

        writer = csv.writer(response)
        writer.writerow(['№', 'Название', 'Количество', 'Единица измерения'])
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
            return Response({'detail': 'Страница не найдена'},
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
            return Response({'detail': 'Страница не найдена'},
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
            return Response({'detail': 'Рецепт не добавлен в список покупок'},
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
            return Response({'detail': 'Рецепт не найден'},
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



class UsersViewSet(djoser_UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserViewSerializer
    permission_classes = [AllowAny, IsUserSelfOrCreateAndReadOnly]
    filterset_fields = []

    def get_serializer_class(self):
        if self.action == 'create':
            return UserAddSerializer
        return UserViewSerializer

    @action(detail=False, methods=['POST'],
            permission_classes=[IsAuthenticated],
            url_path='set_password', url_name='set-password')
    def set_password(self, request):
        """Изменить пароль текущего пользователя"""
        user = request.user

        serializer = PasswordChangeSerializer(data=request.data,
                                              context=self.get_serializer_context())
        if serializer.is_valid() and user.check_password(
                serializer.validated_data['current_password']):
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    # @action(detail=False, methods=['GET'],
    #         permission_classes=[IsAuthenticated],
    #         url_path='me', url_name='me')
    # def me(self, request):
    #     """Текущий пользователь"""
    #     instance = request.user
    #     serializer = self.get_serializer(instance=instance)
    #     return Response(serializer.data)

    @action(detail=False, methods=['PUT', 'DELETE'],
            permission_classes=[IsAuthenticated],
            url_path='me/avatar', url_name='me-avatar')
    def me_upload_or_delete_avatar(self, request):
        """Загрузка или удаление аватара текущего пользователя"""
        if request.method == 'DELETE':
            return self._delete_my_avatar(request)
        elif request.method == 'PUT':
            return self._upload_my_avatar(request)
        else:
            return Response({'detail': 'Метод не поддерживается'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def _upload_my_avatar(self, request):
        user = request.user
        serializer = AvatarUploadSerializer(instance=user,
                                            context=self.get_serializer_context(),
                                            data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        resp_serializer = AvatarViewSerializer(instance=user,
                                               context=self.get_serializer_context())
        return Response(resp_serializer.data,
                        status=status.HTTP_200_OK)

    def _delete_my_avatar(self, request):
        user = request.user
        if user.avatar:
            os.remove(user.avatar.path)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated],
            url_path='subscriptions', url_name='subscriptions')
    def subscriptions(self, request):
        """Мои подписки"""
        user = request.user

        recipes_limit = request.query_params.get('recipes_limit', None)

        if recipes_limit:
            limited_subq = (Recipe.objects.filter(author=OuterRef('author'))
                            .order_by('id').values('id')[:int(recipes_limit)])
            qs = Recipe.objects.filter(id__in=Subquery(limited_subq))
        else:
            qs = Recipe.objects.all()

        queryset = (User.objects.filter(subscriptions_on_me__follower=user)
                    .prefetch_related(Prefetch(
            'recipes',
            queryset=qs,
        )).annotate(recipes_count=Count('recipes')))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserWithRecipesSerializer(page, many=True,
                                                   context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)
        else:
            serializer = UserWithRecipesSerializer(queryset, many=True,
                                                   context=self.get_serializer_context())
            return Response(serializer.data)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated],
            url_path='subscribe', url_name='subscribe-unsubscribe')
    def subscribe_unsubscribe(self, request, pk=None):
        """Подписаться или отписаться на пользователя"""
        user = request.user
        author = self.get_object()
        if user == author:
            return Response({'detail': 'Нельзя подписаться на себя'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            recipes_limit = request.query_params.get('recipes_limit', None)
            return self._subscribe(user, author, recipes_limit)
        elif request.method == 'DELETE':
            return self._unsubscribe(user, author)
        else:
            return Response({'detail': 'Метод не поддерживается'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def _subscribe(self, user, author, recipes_limit=None):
        if Subscription.objects.filter(author=author, follower=user).count() > 0:
            return Response({'detail': 'Вы уже подписаны на данного пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)
        Subscription.objects.create(author=author, follower=user)
        if recipes_limit:
            author.recipes_limited = author.recipes.all()[:int(recipes_limit)]
        serializer = UserWithRecipesSerializer(instance=author,
                                               context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _unsubscribe(self, user, author):
        """Отписаться от пользователя"""
        try:
            subscr = Subscription.objects.get(author=author, follower=user)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Вы не подписаны на данного пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)
        subscr.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
