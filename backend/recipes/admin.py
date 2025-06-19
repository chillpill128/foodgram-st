from django.contrib import admin

from .models import (
    Recipe, RecipeIngredients, Ingredient, ShoppingCart
)


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
