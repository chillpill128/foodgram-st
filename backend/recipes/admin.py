from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db.models import Count

from .models import (
    Recipe, RecipeIngredients, Ingredient, ShoppingCart,
    User, Subscription
)


class SubscriptionAdmin(admin.TabularInline):
    model = Subscription
    fk_name = 'follower'
    fields = ['author']
    extra = 1


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['pk', 'email', 'username', 'first_name', 'last_name']
    inlines = [SubscriptionAdmin]
    readonly_fields = ['pk', 'groups', 'user_permissions', 'last_login']



@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'measurement_unit']
    readonly_fields = ['pk']


class RecipeIngredientInlineAdmin(admin.TabularInline):
    model = RecipeIngredients
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        'pk', 'name', 'cooking_time', 'author',
        'favorites_count', 'ingredients_list', 'image_preview'
    ]
    list_display_links = ['pk', 'name']
    readonly_fields = ['pk', 'image_preview']
    inlines = [RecipeIngredientInlineAdmin]
    list_select_related = ['author']
    list_filter = ['author', 'cooking_time']
    search_fields = ['name', 'ingredients__name']
    ordering = ['-created_at']
    sortable_by = ['pk', 'name', 'cooking_time', 'author']

    def get_queryset(self, request):
        recipes_qs = super().get_queryset(request)
        recipes_qs = recipes_qs.annotate(
            _favorites_count=Count('favorites', distinct=True)
        )
        return recipes_qs

    @mark_safe
    def ingredients_list(self, obj):
        ingredients = obj.ingredients.all()
        items = [f"<li>{ingredient.name}</li>" for ingredient in ingredients]
        return f"<ul>{''.join(items)}</ul>"
    ingredients_list.short_description = 'Ингредиенты'

    @mark_safe
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 130px;" />'
        return 'Нету'
    image_preview.short_description = 'Превью'

    def favorites_count(self, obj):
        return obj._favorites_count
    favorites_count.admin_order_field = '_favorites_count'
    favorites_count.short_description = 'В избранном'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['pk', 'user', 'recipe']
    readonly_fields = ['pk']
