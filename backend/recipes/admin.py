from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as auth_UserAdmin
from django.utils.safestring import mark_safe
from django.db.models import Count

from .models import (
    Recipe, RecipeIngredients, Ingredient, ShoppingCart,
    User, Subscription, FavoriteRecipe
)


class SubscriptionInlineAdmin(admin.TabularInline):
    model = Subscription
    fk_name = 'follower'
    fields = ['author']
    extra = 1

class FavoriteRecipeInlineAdmin(admin.TabularInline):
    model = FavoriteRecipe
    fk_name = 'user'
    fields = ['recipe']
    extra = 1

class ShoppingCartInlineAdmin(admin.TabularInline):
    model = ShoppingCart
    fk_name = 'user'
    fields = ['recipe']
    extra = 1


class BaseHasSomethingFilter(admin.SimpleListFilter):
    item_to_filter = ''
    lookup_choices = [('yes', 'Да'), ('no', 'Нет')]

    def queryset(self, request, user_qs):
        if self.value() == 'yes':
            return user_qs.filter(**{f'{self.item_to_filter}__gte': 1})
        elif self.value() == 'no':
            return user_qs.filter(**{self.item_to_filter: 0})
        return user_qs


class HasRecipesFilter(BaseHasSomethingFilter):
    item_to_filter = '_recipes_count'
    title = 'Есть рецепты'
    parameter_name = 'has-recipes'

class HasAuthorsFilter(BaseHasSomethingFilter):
    item_to_filter = '_authors_count'
    title = 'Есть подписки'
    parameter_name = 'has-authors'

class HasFollowersFilter(BaseHasSomethingFilter):
    item_to_filter = '_followers_count'
    title = 'Есть подписчики'
    parameter_name = 'has-followers'


@admin.register(User)
class UserAdmin(auth_UserAdmin):
    list_display = ['pk', 'username', 'full_name', 'email', 'avatar_preview',
                    'recipes_count', 'authors_count', 'followers_count']
    list_display_links = ['pk', 'username']
    inlines = [SubscriptionInlineAdmin, FavoriteRecipeInlineAdmin, ShoppingCartInlineAdmin]
    readonly_fields = ['pk', 'avatar_preview', 'full_name',
                       'followers_count', 'recipes_count', 'authors_count',
                       'groups', 'last_login', 'user_permissions']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Аватар', {'fields': ('avatar',)}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'username')}),
        ('Доступ', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Разное', {'fields': ('recipes_count', 'followers_count', 'authors_count')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    list_filter = [HasRecipesFilter, HasFollowersFilter, HasAuthorsFilter]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    sortable_by = ['pk', 'username', 'full_name', 'email',
                   'recipes_count', 'authors_count', 'followers_count']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _followers_count=Count('subscriptions_author', distinct=True),
            _authors_count=Count('subscriptions_follower', distinct=True),
            _recipes_count=Count('recipes', distinct=True),
        )

    @admin.display(ordering='first_name', description='ФИО')
    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    @admin.display(ordering='_recipes_count', description='Рецептов')
    def recipes_count(self, obj):
        return obj._recipes_count

    @admin.display(ordering='_followers_count', description='Подписчиков')
    def followers_count(self, obj):
        return obj._followers_count

    @admin.display(ordering='_authors_count', description='Подписок')
    def authors_count(self, obj):
        return obj._authors_count

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_preview(self, obj):
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" style="max-height: 100px; max-width: 130px;" />'
        return 'Нету'


class IsInRecipesFilter(BaseHasSomethingFilter):
    title = 'Присутствует в рецептах'
    parameter_name = 'in-recipes'
    item_to_filter = '_recipes_count'



@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'measurement_unit', 'recipes_count']
    list_display_links = ['pk', 'name']
    readonly_fields = ['pk', 'recipes_count']
    list_filter = ['measurement_unit', IsInRecipesFilter]
    search_fields = ['name', 'measurement_unit']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _recipes_count=Count('recipeingredients', distinct=True)
        )

    @admin.display(ordering='_recipes_count', description='Рецептов')
    def recipes_count(self, obj):
        return obj._recipes_count


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
    sortable_by = ['pk', 'name', 'cooking_time', 'author', 'favorites_count']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _favorites_count=Count('favorites', distinct=True)
        )

    @admin.display(description='Ингредиенты')
    @mark_safe
    def ingredients_list(self, obj):
        return '<br/>'.join(
            f'{ri.ingredient.name} - {ri.amount} {ri.ingredient.measurement_unit}'
            for ri in obj.recipeingredients.all().select_related('ingredient')
        )

    @admin.display(description='Превью')
    @mark_safe
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 130px;" />'
        return 'Нету'

    @admin.display(ordering='_favorites_count', description='В избранном')
    def favorites_count(self, obj):
        return obj._favorites_count


class UserRecipeAdminMixin:
    list_display = ['pk', 'user', 'recipe']
    readonly_fields = ['pk']
    list_select_related = ['user', 'recipe']


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UserRecipeAdminMixin, admin.ModelAdmin):
    pass


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(UserRecipeAdminMixin, admin.ModelAdmin):
    pass
