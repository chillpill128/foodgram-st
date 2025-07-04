import os
import datetime
from django.conf import settings
from django.http import FileResponse
from django.db.models import BooleanField, Count, Q, OuterRef, Prefetch, Sum, Subquery
from django.db.models.functions import Lower
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

    @staticmethod
    def perform_save(serializer):
        recipe = serializer.save()
        recipe.is_favorited = recipe.favorites.count() > 0
        recipe.is_in_shopping_cart = recipe.shopping_carts.count() > 0
        serializer.instance = recipe

    def perform_update(self, serializer):
        self.perform_save(serializer)

    def perform_create(self, serializer):
        self.perform_save(serializer)

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
                f'{n+1},\t{ing.name.capitalize()},\t{ing.amount},\t{ing.measurement_unit}'
                for n, ing in enumerate(ingredients)
            ]),
            '\nСписок рецептов, для которых эти продукты:',
            '№,\tНазвание,\tАвтор'
            '\n'.join([
                f'{n+1},\t{recipe.name.capitalize()},\t{recipe.author}'
                for n, recipe in enumerate(recipes)
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
            raise status.HTTP_404_NOT_FOUND
        short_link = f'/{settings.RECIPE_SHORT_LINK_BASE_PATH}/{pk}'
        return Response({
            'short-link': self.request.build_absolute_uri(short_link)
        })

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated],
            url_path='shopping_cart', url_name='add-delete-shopping-cart')
    def add_delete_shopping_cart(self, request, pk=None, *args, **kwargs):
        """Добавить или удалить рецепт из списка покупок"""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if request.method == 'DELETE':
            return self._delete_from_model(
                ShoppingCart, user, recipe,
                f'Рецепт {recipe} не добавлен в список покупок'
            )
        return self._add_to_model(
            ShoppingCart, user, recipe,
            f'Рецепт "{recipe}" уже в списке покупок'
        )

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated],
            url_path='favorite', url_name='add-favorite')
    def add_delete_favorite(self, request, pk=None, *args, **kwargs):
        """Добавить рецепт в избранное"""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if request.method == 'DELETE':
            return self._delete_from_model(
                FavoriteRecipe, user, recipe,
                f'Рецепт "{recipe}" ещё не добавлен в избранное'
            )
        return self._add_to_model(
            FavoriteRecipe, user, recipe,
            f'Рецепт "{recipe}" уже в избранном'
        )

    def _add_to_model(self, model_class, user, recipe,
                      exists_error_text,
                      response_serializer=RecipeShortSerializer):
        _, is_created = model_class.objects.get_or_create(user=user, recipe=recipe)
        if not is_created:
            return Response({'detail': exists_error_text},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(response_serializer(
                instance=recipe, context=self.get_serializer_context()
            ).data, status=status.HTTP_201_CREATED)

    def _delete_from_model(self, model_class, user, recipe,
                           not_exists_error_text):
        get_object_or_404(model_class, user=user, recipe=recipe).delete()
        # try:
        #     item = model_class.objects.get(
        #         user=user, recipe=recipe)
        # except model_class.DoesNotExist:
        #     return Response({'detail': not_exists_error_text},
        #                     status=status.HTTP_400_BAD_REQUEST)
        # item.delete()
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
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    filterset_fields = []

    def get_queryset(self):
        users_qs = super().get_queryset()
        user = self.request.user

        if user.is_authenticated:
            users_qs = users_qs.annotate(is_subscribed=Count(
                'followers__follower_id',
                filter=Q(followers__follower=user),
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

        recipes_limit = request.query_params.get('recipes_limit', None)

        if recipes_limit:
            limited_subq = Recipe.objects.filter(author=OuterRef('author')) \
                .order_by('id').values('id')[:int(recipes_limit)]
            recipes_qs = Recipe.objects.filter(id__in=Subquery(limited_subq))
        else:
            recipes_qs = Recipe.objects.all()

        users_qs = User.objects.filter(followers__follower=user) \
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
        if user == author:
            return Response(
                {'detail': 'Нельзя отписаться от самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        get_object_or_404(Subscription, author=author, follower=user).delete()
        # try:
        #     subscr = Subscription.objects.get(author=author, follower=user)
        # except Subscription.DoesNotExist:
        #     return Response(
        #         {'detail': f'Вы не подписаны на пользователя: {author}'},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        # subscr.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
