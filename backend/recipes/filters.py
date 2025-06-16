from django_filters import rest_framework as filters

from .models import Recipe

"""Доступна фильтрация по избранному, автору и списку покупок."""

class RecipeFilterSet(filters.FilterSet):
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        if value == 1:
            queryset = queryset.filter(favorite__user=user)
        elif value == 0:
            queryset = queryset.exclude(favorite__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        if value == 1:
            return queryset.filter(shopping_cart__user=user)
        elif value == 0:
            return queryset.exclude(shopping_cart__user=user)
        return queryset
