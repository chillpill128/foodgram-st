from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilterSet(filters.FilterSet):
    """Доступна фильтрация по избранному, автору и списку покупок."""
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, recipe_queryset, name, value):
        user = self.request.user
        return self._filter_by_user(recipe_queryset, user, 'favorites__user', value)

    def filter_is_in_shopping_cart(self, recipe_queryset, name, value):
        user = self.request.user
        return self._filter_by_user(recipe_queryset, user, 'shopping_carts__user', value)

    @staticmethod
    def _filter_by_user(recipe_queryset, user, path_to_user, value):
        if not user.is_authenticated:
            return recipe_queryset.none() if value == 1 else recipe_queryset

        if value == 1:
            recipe_queryset = recipe_queryset.filter(**{path_to_user: user})
        elif value == 0:
            recipe_queryset = recipe_queryset.exclude(**{path_to_user: user})
        return recipe_queryset
