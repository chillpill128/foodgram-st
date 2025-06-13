from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Ingredient(models.Model):
    name = models.CharField(_('Название'))
    measurement_unit = models.CharField(_('единица измерения'))

    class Meta:
        verbose_name = _('Ингридиент')
        verbose_name_plural = _('Ингридиенты')


class Recipe(models.Model):
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(to=Ingredient,
                                         related_name='recipes',
                                         verbose_name=_('Ингридиенты'),
                                         through='RecipeIngredients')
    is_favorited = models.BooleanField(_('В избранном'), default=False)
    is_in_shopping_cart = models.BooleanField(_('В корзине'), default=False)
    name = models.CharField(_('Название'), max_length=256)
    image = models.ImageField(_('Картинка'))
    text = models.TextField(_('Описание'))
    cooking_time = models.PositiveIntegerField(_('Время приготовления'))

    class Meta:
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='recipeingredients',
                               on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, related_name='recipeingredients',
                                   on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(_('Количество'), default=1)

    class Meta:
        unique_together = ['recipe', 'ingredient']
        verbose_name = _('Ингридиент в рецепте')
        verbose_name_plural = _('Ингридиенты в рецептах')


class ShoppingCart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='shopping_cart',on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='shopping_cart', on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'recipe']
        verbose_name = _('Рецепт в корзине')
        verbose_name_plural = _('Рецепты в корзине')

