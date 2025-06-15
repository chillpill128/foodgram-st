from django.contrib import admin

from .models import (
    Recipe, RecipeIngredients, Ingredient, ShoppingCart
)


admin.site.register(Ingredient)
admin.site.register(ShoppingCart)
admin.site.register(RecipeIngredients)
admin.site.register(Recipe)


# class RecipeIngredientInlineAdmin(admin.TabularInline):
#     model = RecipeIngredients
#     extra = 1
#
#
# @admin.register(Recipe)
# class RecipeAdmin(admin.ModelAdmin):
#     list_display = ['pk', 'author', 'name', 'text', 'cooking_time']
#     readonly_fields = ['pk']
#     inlines = [RecipeIngredientInlineAdmin]
