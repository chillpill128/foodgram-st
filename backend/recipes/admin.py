from django.contrib import admin

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
    list_display = ['pk', 'author', 'name', 'text', 'cooking_time']
    readonly_fields = ['pk']
    inlines = [RecipeIngredientInlineAdmin]


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['pk', 'user', 'recipe']
    readonly_fields = ['pk']
