import os
import datetime
from django.http import FileResponse
from django.db.models import BooleanField, Count, Q, Sum
from django.db.models.functions import Lower
from django.urls import reverse
from djoser.views import UserViewSet as djoser_UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import IsAuthor
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
)
from .serializers.users import (
    UserSerializer,
    RecipeShortSerializer,
    UserWithRecipesSerializer,
    AvatarUploadSerializer,
)


class RecipesViewSet(ModelViewSet):
    """Рецепты"""
    queryset = Recipe.objects.all().prefetch_related(
        'recipeingredients',
        'recipeingredients__ingredient'
    )
    serializer_class = RecipeViewSerializer
    filterset_class = RecipeFilterSet
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ('destroy', 'update', 'partial_update'):
            return [IsAuthor()]

        return super().get_permissions()

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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['GET'], detail=False, permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart', url_name='download-shopping-cart')
    def download_shopping_cart(self, request, *args, **kwargs):
        """Скачать список покупок в csv-формате"""
        user = request.user

        ingredients = Ingredient.objects.filter(
            recipeingredients__recipe__shopping_carts__user=user
        ).distinct().order_by(Lower('name')).annotate(
            amount=Sum('recipeingredients__amount')
        )
        recipes = Recipe.objects.filter(shopping_carts__user=user) \
            .select_related('author') \
            .order_by('name')
        current_date = datetime.datetime.now().strftime('%d.%m.%Y')

        output_text = '\n'.join([
            f'Список продуктов. Сформирован {current_date}',
            '№,\tНазвание,\tКоличество,\tЕдиница измерения'
            '\n'.join([
                f'{n},\t{ing.name.capitalize()},\t{ing.amount},\t{ing.measurement_unit}'
                for n, ing in enumerate(ingredients, start=1)
            ]),
            '\nСписок рецептов, для которых эти продукты:',
            '№,\tНазвание,\tАвтор'
            '\n'.join([
                f'{n},\t{recipe.name.capitalize()},\t{recipe.author}'
                for n, recipe in enumerate(recipes, start=1)
            ]),
        ])
        response = FileResponse(output_text, filename='Покупки.txt', as_attachment=True)
        return response

    @action(methods=['GET'], detail=True,
            permission_classes=[AllowAny],
            url_path='get-link', url_name='get-short-link')
    def get_link(self, request, pk=None, *args, **kwargs):
        """Получить короткую ссылку"""
        if not Recipe.objects.filter(pk=pk).exists():
            return Response({
                'detail': f'Рецепт с данным id ({pk}) не существует!'
            }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'short-link': self.request.build_absolute_uri(
                reverse('recipe-short-link-redirect', kwargs={'recipe_id': pk})
            )
        })

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated],
            url_path='shopping_cart', url_name='add-delete-shopping-cart')
    def add_delete_shopping_cart(self, request, pk=None, *args, **kwargs):
        """Добавить или удалить рецепт из списка покупок"""
        user = request.user
        if request.method == 'DELETE':
            return self._delete_from_model(ShoppingCart, user, pk)
        return self._add_to_model(ShoppingCart, user, pk)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated],
            url_path='favorite', url_name='add-favorite')
    def add_delete_favorite(self, request, pk=None, *args, **kwargs):
        """Добавить рецепт в избранное"""
        user = request.user
        if request.method == 'DELETE':
            return self._delete_from_model(FavoriteRecipe, user, pk)
        return self._add_to_model(FavoriteRecipe, user, pk)

    def _add_to_model(self, model_class, user, recipe_pk):
        recipe = get_object_or_404(Recipe, pk=recipe_pk)
        _, is_created = model_class.objects.get_or_create(user=user, recipe=recipe)
        if not is_created:
            return Response({
                'detail': f'Рецепт "{recipe}" уже добавлен в {model_class._meta.verbose_name}'
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response(RecipeShortSerializer(
                instance=recipe, context=self.get_serializer_context()
            ).data, status=status.HTTP_201_CREATED)

    def _delete_from_model(self, model_class, user, recipe_pk):
        get_object_or_404(model_class, user=user, recipe_id=recipe_pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Ингридиенты"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    search_fields = ['^name']
    filterset_fields = ['name']
    pagination_class = None


class UsersViewSet(djoser_UserViewSet):
    """Пользователи"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    filterset_fields = []

    def get_queryset(self):
        users_qs = super().get_queryset()
        user = self.request.user

        if user.is_authenticated:
            users_qs = users_qs.annotate(is_subscribed=Count(
                'subscriptions_author__follower_id',
                filter=Q(subscriptions_author__follower=user),
                output_field=BooleanField()
            ))
        return users_qs

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
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
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        users_qs = User.objects.filter(subscriptions_author__follower=user) \
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

        recipes_limit = request.query_params.get('recipes_limit', None)
        return self._subscribe(user, author, recipes_limit)

    def _subscribe(self, user, author, recipes_limit=None):
        if user == author:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        _, is_created = Subscription.objects.get_or_create(
            author=author, follower=user
        )
        if not is_created:
            return Response(
                {'detail': f'Вы уже подписаны на пользователя: {author}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if recipes_limit:
            author.recipes_limited = author.recipes.all()[:int(recipes_limit)]
        serializer = UserWithRecipesSerializer(
            instance=author,
            context=self.get_serializer_context()
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _unsubscribe(self, user, author):
        """Отписаться от пользователя"""
        get_object_or_404(Subscription, author=author, follower=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
