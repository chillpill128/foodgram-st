import io
import os
import datetime
from django.http import FileResponse
from django.db.models import  BooleanField, Count, Q, OuterRef, Prefetch, Sum, Subquery
from djoser.views import UserViewSet as djoser_UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    AllowAny, IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import (
    IsAuthorOrCreateAndReadOnly, IsUserSelfOrCreateAndReadOnly
)
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    ShoppingCart,
    User,
    Subscription
)
from .filters import RecipeFilterSet
from .serializers.recipes import (
    IngredientSerializer,
    RecipeViewSerializer,
    RecipeChangeSerializer,
    RecipeShortLinkSerializer,
)
from .serializers.users import (
    UserSerializer,
    UserWithRecipesSerializer,
    AvatarViewSerializer,
    AvatarUploadSerializer,
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
        recipes_qs = super().get_queryset()
        if user.is_authenticated:
            recipes_qs = recipes_qs.annotate(
                is_favorited=Count(
                    'favorites__id',
                    filter=Q(favorites__user=user),
                    output_field=BooleanField()
                ),
                is_in_shopping_cart=Count(
                    'shopping_carts__id',
                    filter=Q(shopping_carts__user=user),
                    output_field=BooleanField()
                ))
        return recipes_qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeChangeSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipe = serializer.save()
        recipe.is_favorited = 1 if recipe.favorites.count() > 0 else 0
        recipe.is_in_shopping_cart = 1 if recipe.shopping_carts.count() > 0 else 0

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
        recipe.is_favorited = 1 if recipe.favorites.count() > 0 else 0
        recipe.is_in_shopping_cart = 1 if recipe.shopping_carts.count() > 0 else 0
        serializer_resp = RecipeViewSerializer(
            instance=recipe,
            context=self.get_serializer_context()
        )
        return Response(serializer_resp.data)

    @action(methods=['GET'], detail=False, permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart', url_name='download-shopping-cart')
    def download_shopping_cart(self, request, *args, **kwargs):
        """Скачать список покупок в csv-формате"""
        user = request.user

        ingredients = Ingredient.objects.filter(
            recipeingredients__recipe__shopping_carts__user=user
        ).distinct().order_by('name').annotate(
            amount=Sum('recipeingredients__amount')
        )
        recipes = Recipe.objects.filter(shopping_carts__user=user) \
            .select_related('author') \
            .order_by('name')
        current_date = datetime.datetime.now().strftime('%d.%m.%Y')

        buffer = io.StringIO()
        buffer.write('\n'.join([
            f'Список продуктов. Сформирован {current_date}',
            ',\t'.join(['№', 'Название', 'Количество', 'Единица измерения']),
            '\n'.join([
                ',\t'.join(
                    [str(n), ing.name.capitalize(), str(ing.amount),
                     str(ing.measurement_unit)])
                for n, ing in enumerate(ingredients)
            ]),
            'Список рецептов, для которых эти продукты:',
            ',\t'.join(['№', 'Название', 'Автор']),
            '\n'.join([
                ',\t'.join([str(n), recipe.name.capitalize(), str(recipe.author)])
                for n, recipe in enumerate(recipes)
            ]),
        ]))
        response = FileResponse(buffer, filename='Покупки.txt', as_attachment=True)
        response['Content-Type'] = 'text/plain'
        return response

    @action(methods=['GET'], detail=True,
            permission_classes=[AllowAny],
            url_path='get-link', url_name='get-short-link')
    def get_link(self, request, pk=None, *args, **kwargs):
        """Получить короткую ссылку"""
        recipe = get_object_or_404(Recipe, pk=pk)

        return Response(RecipeShortLinkSerializer(
            instance=recipe,
            context=self.get_serializer_context()
        ).data)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated],
            url_path='shopping_cart', url_name='add-delete-shopping-cart')
    def add_delete_shopping_cart(self, request, pk=None, *args, **kwargs):
        """Добавить или удалить рецепт из списка покупок"""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'DELETE':
            return self._delete_from_shopping_cart(recipe, user)
        else:
            return self._add_to_shopping_cart(recipe, user)

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
    def add_delete_favorite(self, request, pk=None, *args, **kwargs):
        """Добавить рецепт в избранное"""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'DELETE':
            return self._delete_from_favorite(recipe, user)
        else:
            return self._add_to_favorite(recipe, user)

    def _add_to_favorite(self, recipe, user):
        if FavoriteRecipe.objects.filter(user=user, recipe=recipe).count() != 0:
            return Response(
                {'detail': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        FavoriteRecipe.objects.create(user=user, recipe=recipe)
        return Response(
            RecipeShortenSerializer(
                instance=recipe,
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
    serializer_class = UserSerializer
    permission_classes = [AllowAny, IsUserSelfOrCreateAndReadOnly]
    filterset_fields = []

    def get_queryset(self):
        users_qs = super().get_queryset()
        user = self.request.user

        if user.is_authenticated:
            users_qs = users_qs.annotate(is_subscribed=Count(
                'followers__id',
                filter=Q(followers=user),
                output_field=BooleanField()
            ))
        return users_qs

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(detail=False, methods=['PUT', 'DELETE'],
            permission_classes=[IsAuthenticated],
            url_path='me/avatar', url_name='me-avatar')
    def me_upload_or_delete_avatar(self, request, *args, **kwargs):
        """Загрузка или удаление аватара текущего пользователя"""
        if request.method == 'DELETE':
            return self._delete_my_avatar(request)
        else:
            return self._upload_my_avatar(request)

    def _upload_my_avatar(self, request):
        user = request.user
        serializer = AvatarUploadSerializer(
            instance=user,
            context=self.get_serializer_context(),
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        serializer_resp = AvatarViewSerializer(
            instance=user,
            context=self.get_serializer_context(),
        )
        return Response(serializer_resp.data, status=status.HTTP_200_OK)

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
    def subscriptions(self, request, *args, **kwargs):
        """Мои подписки"""
        user = request.user

        recipes_limit = request.query_params.get('recipes_limit', None)

        if recipes_limit:
            limited_subq = Recipe.objects.filter(author=OuterRef('author')) \
                .order_by('id').values('id')[:int(recipes_limit)]
            recipes_qs = Recipe.objects.filter(id__in=Subquery(limited_subq))
        else:
            recipes_qs = Recipe.objects.all()

        users_qs = User.objects.filter(subscriptions_on_me__follower=user) \
            .prefetch_related(Prefetch('recipes', queryset=recipes_qs)) \
            .annotate(recipes_count=Count('recipes'))
        page = self.paginate_queryset(users_qs)
        serializer = UserWithRecipesSerializer(
            page, many=True, context=self.get_serializer_context()
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated],
            url_path='subscribe', url_name='subscribe-unsubscribe')
    def subscribe_unsubscribe(self, request, pk=None, *args, **kwargs):
        """Подписаться или отписаться на пользователя"""
        user = request.user
        author = self.get_object()

        if request.method == 'DELETE':
            return self._unsubscribe(user, author)
        else:
            recipes_limit = request.query_params.get('recipes_limit', None)
            return self._subscribe(user, author, recipes_limit)

    def _subscribe(self, user, author, recipes_limit=None):
        if user == author:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(author=author, follower=user).exists():
            return Response(
                {'detail': f'Вы уже подписаны на пользователя: {author}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(author=author, follower=user)
        if recipes_limit:
            author.recipes_limited = author.recipes.all()[:int(recipes_limit)]
        serializer = UserWithRecipesSerializer(
            instance=author,
            context=self.get_serializer_context()
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _unsubscribe(self, user, author):
        """Отписаться от пользователя"""
        if user == author:
            return Response(
                {'detail': 'Нельзя отписаться от самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            subscr = Subscription.objects.get(author=author, follower=user)
        except Subscription.DoesNotExist:
            return Response(
                {'detail': f'Вы не подписаны на пользователя: {author}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscr.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
